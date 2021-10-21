import attr
from ranzen import implements

from conduit.data import CdtDataModule, CdtVisionDataModule, TrainValTestSplit
from conduit.data.datasets.vision.dummy import DummyVisionDataset


@attr.define(kw_only=True)
class DummyVisionDataModule(CdtVisionDataModule):
    num_samples: int = 1_000
    seed: int = 8
    root: str = ""
    height: int = 32
    width: int = 32
    channels: int = 3
    batch_size: int = 32
    s_card: int = 2
    y_card: int = 2

    @implements(CdtDataModule)
    def _get_splits(self) -> TrainValTestSplit:
        # Split the data randomly according to val- and test-prop
        data = DummyVisionDataset(
            channels=self.channels,
            height=self.height,
            width=self.width,
            num_samples=self.num_samples,
            s_card=self.s_card,
            y_card=self.y_card,
        )
        val_data, test_data, train_data = data.random_split(props=(self.val_prop, self.test_prop))
        return TrainValTestSplit(train=train_data, val=val_data, test=test_data)