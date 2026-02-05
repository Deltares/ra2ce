import pytest

from ra2ce.analysis.losses.losses_input_data_reader_base import (
    LossesInputDataReaderBase,
)


class TestLossesInputDataReaderBase:
    def test_initialize_base_raises(self):
        # 1. Define test data
        # Disclaimer: Done like this as in Python 3.11 the exception error differs slightly.
        _expected_class_str = f"Can't instantiate abstract class {LossesInputDataReaderBase.__name__}"
        _expected_methods_str = "abstract method"
        _expected_methods_list = [
            "_parse_df"
        ]

        # 2. Run test
        with pytest.raises(TypeError) as exc_info:
            LossesInputDataReaderBase()

        # 3. Verify expectations
        _exception_mssg = str(exc_info.value)
        assert _expected_class_str in _exception_mssg
        assert _expected_methods_str in _exception_mssg
        for method in _expected_methods_list:
            assert method in _exception_mssg
