# Generated by configen, do not edit.
# See https://github.com/facebookresearch/hydra/tree/master/tools/configen
# fmt: off
# isort:skip_file
# flake8: noqa

from dataclasses import dataclass, field
from builtins import dict
from conduit.data.datasets.vision.celeba import CelebAttr
from conduit.data.datasets.vision.nico import NicoSuperclass
from ranzen.torch.data import TrainingMode
from omegaconf import MISSING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


@dataclass
class CelebADataModuleConf:
    _target_: str = "conduit.data.datamodules.CelebADataModule"
    train_batch_size: int = 64
    eval_batch_size: Optional[int] = None
    val_prop: float = 0.2
    test_prop: float = 0.2
    num_workers: int = 0
    seed: int = 47
    persist_workers: bool = False
    pin_memory: bool = True
    stratified_sampling: bool = False
    instance_weighting: bool = False
    training_mode: TrainingMode = TrainingMode.epoch
    root: Any = MISSING  # Union[str, Path]
    train_transforms: Any = None  # Union[Compose, BasicTransform, Callable[[Image], Any], NoneType]
    test_transforms: Any = None  # Union[Compose, BasicTransform, Callable[[Image], Any], NoneType]
    image_size: int = 224
    superclass: CelebAttr = CelebAttr.Smiling
    subclass: CelebAttr = CelebAttr.Male
    use_predefined_splits: bool = False


@dataclass
class ColoredMNISTDataModuleConf:
    _target_: str = "conduit.data.datamodules.ColoredMNISTDataModule"
    train_batch_size: int = 64
    eval_batch_size: Optional[int] = None
    val_prop: float = 0.2
    test_prop: float = 0.2
    num_workers: int = 0
    seed: int = 47
    persist_workers: bool = False
    pin_memory: bool = True
    stratified_sampling: bool = False
    instance_weighting: bool = False
    training_mode: TrainingMode = TrainingMode.epoch
    root: Any = MISSING  # Union[str, Path]
    train_transforms: Any = None  # Union[Compose, BasicTransform, Callable[[Image], Any], NoneType]
    test_transforms: Any = None  # Union[Compose, BasicTransform, Callable[[Image], Any], NoneType]
    image_size: int = 32
    use_predefined_splits: bool = False
    label_map: Optional[Dict[str, int]] = None
    colors: Optional[List[int]] = None
    num_colors: int = 10
    scale: float = 0.2
    correlation: float = 1.0
    binarize: bool = False
    greyscale: bool = False
    background: bool = False
    black: bool = True


@dataclass
class NICODataModuleConf:
    _target_: str = "conduit.data.datamodules.NICODataModule"
    train_batch_size: int = 64
    eval_batch_size: Optional[int] = None
    val_prop: float = 0.2
    test_prop: float = 0.2
    num_workers: int = 0
    seed: int = 47
    persist_workers: bool = False
    pin_memory: bool = True
    stratified_sampling: bool = False
    instance_weighting: bool = False
    training_mode: TrainingMode = TrainingMode.epoch
    root: Any = MISSING  # Union[str, Path]
    train_transforms: Any = None  # Union[Compose, BasicTransform, Callable[[Image], Any], NoneType]
    test_transforms: Any = None  # Union[Compose, BasicTransform, Callable[[Image], Any], NoneType]
    image_size: int = 224
    class_train_props: Optional[dict] = None
    superclass: NicoSuperclass = NicoSuperclass.animals


@dataclass
class WaterbirdsDataModuleConf:
    _target_: str = "conduit.data.datamodules.WaterbirdsDataModule"
    train_batch_size: int = 64
    eval_batch_size: Optional[int] = None
    val_prop: float = 0.2
    test_prop: float = 0.2
    num_workers: int = 0
    seed: int = 47
    persist_workers: bool = False
    pin_memory: bool = True
    stratified_sampling: bool = False
    instance_weighting: bool = False
    training_mode: TrainingMode = TrainingMode.epoch
    root: Any = MISSING  # Union[str, Path]
    train_transforms: Any = None  # Union[Compose, BasicTransform, Callable[[Image], Any], NoneType]
    test_transforms: Any = None  # Union[Compose, BasicTransform, Callable[[Image], Any], NoneType]
    image_size: int = 224
    use_predefined_splits: bool = False
