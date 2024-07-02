import pytest

from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)


class TestLossesInputDataReaderBase:
    def test_initialize_base_raises(self):
        # 1. Run test
        with pytest.raises(TypeError) as exc_info:
            LossesInputDataReaderBase()

        # 2. Verify expectations
        assert (
            str(exc_info.value)
            == f"Can't instantiate abstract class {LossesInputDataReaderBase.__name__} with abstract method _parse_df"
        )
