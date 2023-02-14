from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString

from ra2ce.analyses.direct.direct_utils import (
    clean_lane_data,
    create_summary_statistics,
    lane_cleaner,
)


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

    def test_clean_lane_data(self):
        # 1. Define test data.
        lane_values = ["0.42;4.2;42", "0.24;2.4;24"]
        _test_lane = pd.Series(lane_values)

        # 2. Run test.
        _result_data = clean_lane_data(_test_lane)

        # 3. Verify expectations.
        assert len(_result_data) == 2
        assert _result_data[0] == 42
        assert _result_data[1] == 24

    def test_create_summary_statistics(self):
        # 1. Define test data.
        _left_line = LineString([[0, 0], [1, 0], [2, 0]])
        _right_line = LineString([[3, 0], [2, 1], [2, 2]])
        _data = {"road_type": ["name1", "name2"], "geometry": [_left_line, _right_line], "lanes": [0, 1]}
        _test_gdf = gpd.GeoDataFrame(_data, crs="EPSG:4326")

        # 2. Run test.
        result_dict = create_summary_statistics(_test_gdf)

        # 3. Verify final expectations
        assert isinstance(result_dict, dict)
