from typing import Any

import numpy as np
import pytest

from ra2ce.analyses.direct.direct_utils import lane_cleaner


class TestDirectUtils:
    @pytest.mark.parametrize(
        "value_type",
        [(None), ("")],
    )
    def test_lane_cleaner_returns_nan(self, value_type: Any):
        assert lane_cleaner(value_type) is np.nan

    def test_lane_cleaner_converts_integer(self):
        _return = lane_cleaner(42)
        assert type(_return) == float

    def test_lane_cleaner_float_returns_value(self):
        assert lane_cleaner(4.2) == 4.2

    @pytest.mark.parametrize("split_char", [(","), (";")])
    def test_lane_cleaner_given_str_list(self, split_char: str):
        _str_value = [".42", "4.2", "42"]
        _clean_value = lane_cleaner(split_char.join(_str_value))
        assert _clean_value == 42

    def test_lane_cleaner_given_str_list_returns_nan(self):
        _str_value = ".42-4.2-42"
        _clean_value = lane_cleaner(_str_value)
        assert _clean_value is np.nan

    @pytest.mark.parametrize("split_char", [(","), (";")])
    def test_lane_cleaner_given_invalid_str_list_returns_nan(self, split_char: str):
        _str_value = ["not", "valid", "list"]
        _clean_value = lane_cleaner(split_char.join(_str_value))
        assert _clean_value is np.nan

    def test_unknown_type_returns_nan(self):
        class DummyClass:
            pass

        assert lane_cleaner(DummyClass()) is np.nan
