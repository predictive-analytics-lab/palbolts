"""Credit Dataset."""
from typing import Literal, Optional

import ethicml as em
from ethicml.preprocessing.scaling import ScalerType
from kit import parsable
from kit.torch import TrainingMode

from .base import TabularDataModule

__all__ = ["CreditDataModule"]


class CreditDataModule(TabularDataModule):
    """Data Module for the Credit Dataset."""

    @parsable
    def __init__(
        self,
        sens_feat: Literal["Sex"] = "Sex",
        disc_feats_only: bool = False,
        # Below are super vars. Not doing *args **kwargs due to this being parsable
        batch_size: int = 100,
        num_workers: int = 0,
        val_prop: float = 0.2,
        test_prop: float = 0.2,
        seed: int = 0,
        persist_workers: bool = False,
        pin_memory: bool = True,
        stratified_sampling: bool = False,
        instance_weighting: bool = False,
        scaler: Optional[ScalerType] = None,
        training_mode: TrainingMode = TrainingMode.epoch,
    ):
        super().__init__(
            batch_size=batch_size,
            num_workers=num_workers,
            val_prop=val_prop,
            test_prop=test_prop,
            seed=seed,
            persist_workers=persist_workers,
            pin_memory=pin_memory,
            stratified_sampling=stratified_sampling,
            instance_weighting=instance_weighting,
            scaler=scaler,
            training_mode=training_mode,
        )
        self.sens_feat = sens_feat
        self.disc_feats_only = disc_feats_only

    @property
    def em_dataset(self) -> em.Dataset:
        return em.credit(split=self.sens_feat, discrete_only=self.disc_feats_only)