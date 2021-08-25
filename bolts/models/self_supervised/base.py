from __future__ import annotations
from abc import abstractmethod
from dataclasses import replace
from typing import Callable, Optional, Sequence

from PIL import Image
from kit.decorators import implements
from kit.misc import gcopy
from kit.torch.data import TrainingMode
import numpy as np
import pytorch_lightning as pl
from pytorch_lightning.utilities.types import EPOCH_OUTPUT, STEP_OUTPUT
import torch
from torch.functional import Tensor
import torch.nn as nn

from bolts.data.datamodules.base import PBDataModule
from bolts.data.datamodules.vision.base import PBVisionDataModule
from bolts.data.datasets.utils import ImageTform
from bolts.data.structures import BinarySample, NamedSample
from bolts.models.base import PBModel
from bolts.models.erm import ERMClassifier
from bolts.models.self_supervised.callbacks import (
    MeanTeacherWeightUpdate,
    PostHocProgressBar,
)
from bolts.models.self_supervised.multicrop import MultiCropOutput
from bolts.types import MetricDict, Stage

__all__ = [
    "InstanceDiscriminator",
    "SelfDistiller",
    "SelfSupervisedModel",
]


class SelfSupervisedModel(PBModel):
    def __init__(
        self,
        *,
        lr: float = 3.0e-4,
        weight_decay: float = 0.0,
        eval_batch_size: int | None = None,
        eval_epochs: int = 100,
    ) -> None:
        super().__init__(lr=lr, weight_decay=weight_decay)
        self.eval_batch_size = eval_batch_size
        self.eval_epochs = eval_epochs
        self._eval_trainer: pl.Trainer | None = None
        self._eval_clf: ERMClassifier | None = None

    @property
    @abstractmethod
    def features(self) -> nn.Module:
        ...

    @property
    def eval_clf(self) -> ERMClassifier:
        if self._eval_clf is None:
            self._eval_clf = self._init_eval_clf()
            self._eval_clf.build(datamodule=self.datamodule, trainer=self.eval_trainer, copy=False)
        return self._eval_clf

    @eval_clf.setter
    def eval_clf(self, clf: ERMClassifier) -> None:
        self._eval_clf = clf

    @property
    def eval_trainer(self) -> pl.Trainer:
        if self._eval_trainer is None:
            self._eval_trainer = gcopy(self.trainer, deep=True, num_sanity_val_batches=0)
            self._eval_trainer.fit_loop.max_epochs = self.eval_epochs
            self._eval_trainer.fit_loop.max_steps = None  # type: ignore
            bar = PostHocProgressBar()
            bar._trainer = self._eval_trainer
            self._eval_trainer.callbacks = [bar]
        return self._eval_trainer

    @eval_trainer.setter
    def eval_trainer(self, trainer: pl.Trainer) -> None:
        self._eval_trainer = trainer

    @abstractmethod
    def _init_eval_clf(self) -> ERMClassifier:
        ...

    @property
    @abstractmethod
    def _eval_train_transform(self) -> ImageTform:
        ...

    def _eval_routine(self) -> None:
        dm_cp = gcopy(
            self.datamodule,
            deep=False,
            stratified_sampling=False,
            training_mode=TrainingMode.epoch,
        )
        if isinstance(dm_cp, PBVisionDataModule):
            dm_cp.train_transforms = self._eval_train_transform
        if self.eval_batch_size is not None:
            dm_cp.train_batch_size = self.eval_batch_size

        self.eval_trainer.fit(
            self.eval_clf,
            train_dataloaders=dm_cp.train_dataloader(),
        )

    @implements(PBModel)
    def inference_step(self, batch: BinarySample, stage: Stage) -> STEP_OUTPUT:
        return self.eval_clf.inference_step(batch=batch, stage=stage)

    @implements(PBModel)
    def inference_epoch_end(self, outputs: EPOCH_OUTPUT, stage: Stage) -> MetricDict:
        results_dict = self.eval_clf.inference_epoch_end(outputs=outputs, stage=stage)
        # Free up memory
        self._eval_clf = None
        return results_dict

    def on_inference_start(self) -> None:
        self._eval_routine()

    @implements(pl.LightningModule)
    def on_validation_start(self) -> None:
        self.on_inference_start()

    @implements(pl.LightningModule)
    def on_test_start(self) -> None:
        self.on_inference_start()


class InstanceDiscriminator(SelfSupervisedModel):
    def __init__(
        self,
        *,
        lr: float,
        weight_decay: float,
        eval_batch_size: int | None,
        eval_epochs: int,
        instance_transforms: Optional[Callable[[Image.Image], Sequence[Tensor]]] = None,
        batch_transforms: Optional[Callable[[Tensor], Tensor]] = None,
    ) -> None:
        super().__init__(
            lr=lr,
            weight_decay=weight_decay,
            eval_batch_size=eval_batch_size,
            eval_epochs=eval_epochs,
        )
        self.instance_transforms = instance_transforms
        self.batch_transforms = batch_transforms

    def _get_positive_views(self, batch: NamedSample) -> MultiCropOutput:
        if isinstance(batch.x, Tensor):
            if self.batch_transforms is None:
                return MultiCropOutput(global_crops=[batch.x, batch.x])
            else:
                view1, view2 = self.batch_transforms(torch.cat([batch.x, batch.x], dim=0)).chunk(
                    2, dim=0
                )
                return MultiCropOutput(global_crops=[view1, view2])
        elif isinstance(batch.x, MultiCropOutput):
            if self.batch_transforms is None:
                return batch.x
            else:
                global_crops = [self.batch_transforms(crop) for crop in batch.x.global_crops]
                local_crops = [self.batch_transforms(crop) for crop in batch.x.local_crops]
                return replace(batch.x, global_crops=global_crops, local_crops=local_crops)
        else:
            raise TypeError("'x' must be  a Tensor or a 'MultiCropTransform' instance.")

    def build(self, datamodule: PBDataModule, *, trainer: pl.Trainer, copy: bool = True) -> None:
        super().build(datamodule=datamodule, trainer=trainer, copy=copy)
        if isinstance(datamodule, PBVisionDataModule):
            datamodule.train_transforms = self.instance_transforms


class SelfDistiller(InstanceDiscriminator):
    student: nn.Module
    teacher: nn.Module

    @torch.no_grad()
    def init_encoders(self) -> tuple[nn.Module, nn.Module]:
        student, teacher = self._init_encoders()
        # there is no backpropagation through the key-encoder, so no need for gradients
        for p in teacher.parameters():
            p.requires_grad = False
        return student, teacher

    @property
    @abstractmethod
    def momentum_schedule(self) -> float | np.ndarray | Tensor:
        ...

    @torch.no_grad()
    @abstractmethod
    def _init_encoders(self) -> tuple[nn.Module, nn.Module]:
        ...

    def build(self, datamodule: PBDataModule, *, trainer: pl.Trainer, copy: bool = True) -> None:
        super().build(datamodule=datamodule, trainer=trainer, copy=copy)
        self.student, self.teacher = self.init_encoders()
        mt_cb = MeanTeacherWeightUpdate(momentum_schedule=self.momentum_schedule)
        if self.trainer.callbacks is None:
            self.trainer.callbacks = [mt_cb]
        else:
            self.trainer.callbacks.append(mt_cb)

    @implements(nn.Module)
    def forward(self, x: Tensor) -> Tensor:
        return self.student(x)
