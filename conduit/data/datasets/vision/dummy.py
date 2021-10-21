from typing import Optional

import numpy as np
from ranzen import implements
import torch

from conduit.data import RawImage
from conduit.data.datasets.vision.base import CdtVisionDataset


class DummyVisionDataset(CdtVisionDataset):
    def __init__(
        self,
        channels: int,
        height: int,
        width: int,
        s_card: Optional[int] = 2,
        y_card: Optional[int] = 2,
        num_samples: int = 10_000,
    ) -> None:
        self.channels = channels
        self.height = height
        self.width = width
        s = torch.randint(s_card, (num_samples,)) if s_card is not None else None
        y = torch.randint(y_card, (num_samples,)) if y_card is not None else None
        x = np.array([""] * num_samples)
        super().__init__(x=x, s=s, y=y, image_dir="")

    @implements(CdtVisionDataset)
    def _load_image(self, index: int) -> RawImage:
        return np.random.randint(
            0, 256, size=(self.height, self.width, self.channels), dtype="uint8"
        )