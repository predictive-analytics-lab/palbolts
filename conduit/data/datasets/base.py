import logging
from typing import (
    ClassVar,
    Generic,
    List,
    Literal,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
    final,
    overload,
)

import numpy as np
import numpy.typing as npt
from ranzen import implements
from ranzen.misc import gcopy
import torch
from torch import Tensor
from typing_extensions import Self

from conduit.data.structures import (
    BinarySample,
    DatasetProt,
    IndexType,
    LoadedData,
    NamedSample,
    SubgroupSample,
    TargetData,
    TernarySample,
    UnloadedData,
)
from conduit.logging import init_logger

__all__ = ["CdtDataset", "I", "S", "X", "Y"]


I = TypeVar(
    "I",
    NamedSample[LoadedData],
    BinarySample[LoadedData],
    SubgroupSample[LoadedData],
    TernarySample[LoadedData],
)

X = TypeVar("X", bound=UnloadedData)
S = TypeVar("S", bound=Optional[Tensor])
Y = TypeVar("Y", bound=Optional[Tensor])


class CdtDataset(DatasetProt[I], Generic[I, X, Y, S]):
    _repr_indent: ClassVar[int] = 4
    _logger: Optional[logging.Logger] = None

    def __init__(
        self, *, x: X, y: Optional[TargetData] = None, s: Optional[TargetData] = None
    ) -> None:
        self.x = x
        if isinstance(y, np.ndarray):
            y = torch.as_tensor(y)
        if isinstance(s, np.ndarray):
            s = torch.as_tensor(s)
        self.y: Y = y if y is None else y.squeeze()
        self.s: S = s if s is None else s.squeeze()

        self._dim_x: Optional[torch.Size] = None
        self._dim_s: Optional[torch.Size] = None
        self._dim_y: Optional[torch.Size] = None
        self._card_y: Optional[int] = None
        self._card_s: Optional[int] = None

    def __repr__(self) -> str:
        head = "Dataset " + self.__class__.__name__
        body = [f"Number of datapoints: {len(self)}"]
        body += self.extra_repr().splitlines()
        lines = [head] + [" " * self._repr_indent + line for line in body]
        return '\n'.join(lines)

    @staticmethod
    def extra_repr() -> str:
        return ""

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = init_logger(self.__class__.__name__)
        return self._logger

    @overload
    def _sample_x(self, index: IndexType, *, coerce_to_tensor: Literal[True] = ...) -> Tensor:
        ...

    @overload
    def _sample_x(self, index: IndexType, *, coerce_to_tensor: Literal[False] = ...) -> LoadedData:
        ...

    def _sample_x(
        self, index: IndexType, *, coerce_to_tensor: bool = False
    ) -> Union[LoadedData, Tensor]:
        x = self.x[index]
        if coerce_to_tensor and (not isinstance(x, Tensor)):
            x = torch.as_tensor(x)
        return x

    def _sample_s(self, index: IndexType) -> Optional[Tensor]:
        if self.s is None:
            return None
        return self.s[index]

    def _sample_y(self, index: IndexType) -> Optional[Tensor]:
        if self.y is None:
            return None
        return self.y[index]

    @property
    @final
    def dim_x(
        self,
    ) -> torch.Size:
        if self._dim_x is None:
            self._dim_x = self._sample_x(0, coerce_to_tensor=True).shape
        return self._dim_x

    @property
    @final
    def dim_s(
        self,
    ) -> torch.Size:
        if self.s is None:
            cls_name = self.__class__.__name__
            raise AttributeError(
                f"'{cls_name}.dim_s' cannot be determined as '{cls_name}.s' is 'None'"
            )
        if self._dim_s is None:
            self._dim_s = torch.Size((1,)) if self.s.ndim == 1 else self.s.shape[1:]
        return self._dim_s

    @property
    @final
    def dim_y(
        self,
    ) -> torch.Size:
        if self.y is None:
            cls_name = self.__class__.__name__
            raise AttributeError(
                f"'{cls_name}.dim_y' cannot be determined as '{cls_name}.y' is 'None'"
            )
        elif self._dim_y is None:
            self._dim_y = torch.Size((1,)) if self.y.ndim == 1 else self.y.shape[1:]
        return self._dim_y

    @property
    @final
    def card_y(
        self,
    ) -> int:
        if self.y is None:
            cls_name = self.__class__.__name__
            raise AttributeError(
                f"'{cls_name}.card_y' cannot be determined as '{cls_name}.y' is 'None'"
            )
        if self._card_y is None:
            self._card_y = len(self.y.unique())
        return self._card_y

    @property
    @final
    def card_s(
        self,
    ) -> int:
        if self.s is None:
            cls_name = self.__class__.__name__
            raise AttributeError(
                f"'{cls_name}.card_s' cannot be determined as '{cls_name}.s' is 'None'"
            )
        if self._card_s is None:
            self._card_s = len(self.s.unique())
        return self._card_s

    def subset(
        self: Self,
        indices: Union[List[int], npt.NDArray[np.uint64], Tensor, slice],
        *,
        deep: bool = False,
    ) -> Self:
        """Create a subset of the dataset from the given indices.

        :param indices: The sample-indices from which to create the subset.
        In the case of being a numpy array or tensor, said array or tensor
        must be 0- or 1-dimensional.

        :param deep: Whether to create a copy of the underlying dataset as
        a basis for the subset. If False then the data of the subset will be
        a view of original dataset's data.

        :returns: A subset of the dataset from the given indices.
        """
        # lazily import make_subset to prevent it being a circular import
        from conduit.data.datasets.utils import make_subset

        return make_subset(dataset=self, indices=indices, deep=deep)

    def random_split(
        self: Self,
        props: Union[Sequence[float], float],
        *,
        deep: bool = False,
        seed: Optional[int] = None,
    ) -> List[Self]:
        """Randomly split the dataset into subsets according to the given proportions.

        :param props: The fractional size of each subset into which to randomly split the data.
        Elements must be non-negative and sum to 1 or less; if less then the size of the final
        split will be computed by complement.

        :param deep: Whether to create a copy of the underlying dataset as
        a basis for the random subsets. If False then the data of the subsets will be
        views of original dataset's data.

        :param seed: PRNG seed to use for sampling.

        :returns: Random subsets of the data of the requested proportions.
        """
        # lazily import ``random_split`` to prevent it being a circular import
        from conduit.data.datasets.utils import random_split

        return random_split(self, props=props, deep=deep, seed=seed)

    @overload
    def cat(self: Self, other: Self, *, inplace: Literal[True] = ..., deep: bool = False) -> None:
        ...

    @overload
    def cat(self: Self, other: Self, *, inplace: Literal[False] = ..., deep: bool = False) -> Self:
        ...

    def cat(
        self: Self, other: Self, *, inplace: bool = False, deep: bool = False
    ) -> Optional[Self]:
        """
        Concatenate this ``self`` with another dataset of the same type.

        :parma other: Other dataset to concatenate with this instance
        :param deep: Whether to create a deep copy of this dataset as the basis for the superset.

        :returns: A concatenation of ``self`` with ``other``.

        .. note::
            All data-independent attributes will be inherited from ``self``.
        """
        superset = self if inplace else gcopy(self, deep=deep)
        xs = [superset.x, other.x]
        if isinstance(superset.x, np.ndarray):
            superset.x = np.concatenate(xs, axis=0)
        else:
            superset.x = torch.cat(cast(List[Tensor], xs), dim=0)
        if (superset.s is not None) and (other.s is not None):
            superset.s = torch.cat([superset.s, other.s], dim=0)
        if (superset.y is not None) and (other.y is not None):
            superset.y = torch.cat([superset.y, other.y], dim=0)

        if not inplace:
            return superset

    @implements(DatasetProt)
    @final
    def __getitem__(self, index: IndexType) -> I:
        x = self._sample_x(index, coerce_to_tensor=False)
        y = self._sample_y(index)
        s = self._sample_s(index)
        # Fetch the appropriate 'Sample' class
        if y is None:
            if s is None:
                sample = NamedSample(x=x)
            else:
                sample = SubgroupSample(x=x, s=s)
        elif s is None:
            sample = BinarySample(x=x, y=y)
        else:
            sample = TernarySample(x=x, y=y, s=s)
        return sample  # type: ignore

    def __len__(self) -> int:
        return len(self.x)

    def __iadd__(self, other: Self) -> Self:
        self.cat(other, inplace=True, deep=False)
        return self

    def __add__(self, other: Self) -> Self:
        return self.cat(other, inplace=False, deep=False)
