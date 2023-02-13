import geopandas as gpd
import pytest
from shapely.geometry import LineString, MultiLineString, Point

from ra2ce.graph.networks_utils import (
    convert_unit,
    drawProgressBar,
    merge_lines_shpfiles,
)


class TestNetworkUtils:
    @pytest.mark.parametrize(
        "unit, expected_result",
        [
            pytest.param("centimeters", 1 / 100, id="cm"),
            pytest.param("meters", 1, id="m"),
            pytest.param("feet", 1 / 3.28084, id="ft"),
        ],
    )
    def test_convert_unit(self, unit: str, expected_result: float):
        assert convert_unit(unit) == expected_result

    @pytest.mark.parametrize("percent", [(-20), (0), (50), (100), (110)])
    def test_draw_progress_bar(self, percent: float):
        drawProgressBar(percent)

    def test_merge_lines_wrong_input_returns(self):
        _left_line = MultiLineString([[[0, 0], [1, 0], [2, 0]]])
        _right_line = MultiLineString([[[3, 0], [2, 1], [2, 2]]])
        _data = {"col1": ["name1", "name2"], "geometry": [_left_line, _right_line]}
        _test_gdf = gpd.GeoDataFrame(_data, crs="EPSG:4326")

        # 2. Run test.
        _merged, _lines_merged = merge_lines_shpfiles(_test_gdf, "sth", ["sth"], 4326)

        # 3. Verify final expectations
        assert _merged.equals(_test_gdf)
        assert _lines_merged.equals(gpd.GeoDataFrame())

    def test_merge_lines_shpfiles(self):
        # 1. Define test data.
        _left_line = LineString([[0, 0], [1, 0], [2, 0]])
        _right_line = LineString([[2, 0], [2, 1], [2, 2]])
        _data = {"col1": ["name1", "name2"], "geometry": [_left_line, _right_line]}
        _test_gdf = gpd.GeoDataFrame(_data, crs="EPSG:4326")

        # 2. Run test.
        _merged, _merged_lines = merge_lines_shpfiles(_test_gdf, "sth", ["sth"], 4326)

        # 3. Verify final expectations.
        assert _merged
        assert _merged_lines
