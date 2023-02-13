import math

import geopandas as gpd
import numpy as np
import pytest
from pyproj import CRS
from shapely.geometry import LineString, MultiLineString, Point

from ra2ce.graph import networks_utils as nu


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
        assert nu.convert_unit(unit) == expected_result

    @pytest.mark.parametrize("percent", [(-20), (0), (50), (100), (110)])
    def test_draw_progress_bar(self, percent: float):
        nu.drawProgressBar(percent)

    def test_merge_lines_automatic_wrong_input_returns(self):
        _left_line = MultiLineString([[[0, 0], [1, 0], [2, 0]]])
        _right_line = MultiLineString([[[3, 0], [2, 1], [2, 2]]])
        _data = {"col1": ["name1", "name2"], "geometry": [_left_line, _right_line]}
        _test_gdf = gpd.GeoDataFrame(_data, crs="EPSG:4326")

        # 2. Run test.
        _merged, _lines_merged = nu.merge_lines_automatic(
            _test_gdf, "sth", ["sth"], 4326
        )

        # 3. Verify final expectations
        assert _merged.equals(_test_gdf)
        assert _lines_merged.equals(gpd.GeoDataFrame())

    @pytest.mark.skip(reason="TODO: Merge expects output with 'geoms' property.")
    def test_merge_lines_automatic(self):
        # 1. Define test data.
        _left_line = LineString([[0, 0], [1, 0], [2, 0]])
        _right_line = LineString([[2, 0], [2, 2], [0, 0]])
        _data = {"col1": ["name1", "name2"], "geometry": [_left_line, _right_line]}
        _test_gdf = gpd.GeoDataFrame(_data, crs="EPSG:4326")

        # 2. Run test.
        _merged, _merged_lines = nu.merge_lines_automatic(
            _test_gdf, "sth", ["sth"], 4326
        )

        # 3. Verify final expectations.
        assert _merged
        assert _merged_lines


class TestLineLength:
    def test_line_length_linestring_geographic(self):
        _crs = CRS.from_user_input(4326)
        assert _crs.is_geographic
        _line = LineString([[0, 0], [1, 0], [2, 0]])

        # 2. Run test.
        _return_value = nu.line_length(_line, _crs)

        # 3. Verify expectations.
        assert _return_value == pytest.approx(222639, 0.0001)

    def test_line_length_multilinestring_geographic(self):
        _crs = CRS.from_user_input(4326)
        assert _crs.is_geographic
        _line = MultiLineString([[[0, 0], [1, 0], [2, 0]]])

        # 2. Run test.
        _return_value = nu.line_length(_line, _crs)

        # 3. Verify expectations.
        assert _return_value == pytest.approx(222638.98, 0.0001)

    def test_line_length_non_supported_doesnot_raise(self):
        _crs = CRS.from_user_input(4326)
        assert _crs.is_geographic
        _line = Point([0, 1])

        # 2. Run test.
        _return_value = nu.line_length(_line, _crs)

        # 3. Verify expectations.
        assert _return_value is np.nan

    def test_line_length_linestring_projected(self):
        # 1. Define test data.
        _crs = CRS.from_user_input(26915)
        assert _crs.is_projected
        _line = LineString([[0, 0], [1, 0], [2, 0]])

        # 2. Run test.
        assert nu.line_length(_line, _crs) == pytest.approx(2.0, 0.001)

    def test_line_length_multilinestring_projected(self):
        # 1. Define test data.
        _crs = CRS.from_user_input(26915)
        assert _crs.is_projected
        _line = MultiLineString([[[0, 0], [1, 0], [2, 0]]])

        # 2. Run test.
        assert nu.line_length(_line, _crs) == pytest.approx(2.0, 0.001)

    def test_line_length_non_supported_projected_doesnot_raise(self):
        _crs = CRS.from_user_input(26915)
        assert _crs.is_projected
        _line = Point([0, 1])

        # 2. Run test.
        _return_value = nu.line_length(_line, _crs)

        # 3. Verify expectations.
        assert _return_value is np.nan


class TestVerticesFromLines:
    def test_with_linestrings(self):
        # 1. Define test data.
        _left_line = LineString([[0, 0], [1, 0], [2, 0]])
        _right_line = LineString([[2, 0], [2, 2], [0, 0]])
        _lines = [_left_line, _right_line]
        _ids = ["t_a", "t_b"]

        # 2. Run test.
        _vertices = nu.vertices_from_lines(_lines, _ids)

        # 3. Verify final expectations.
        assert isinstance(_vertices, dict)
        assert list(_vertices.keys()) == _ids

    def test_with_multilinestrings(self):
        # 1. Define test data.
        _left_line = MultiLineString([[[0, 0], [1, 0], [2, 0]]])
        _right_line = MultiLineString([[[1, 1], [2, 2], [3, 3]]])
        _lines = [_left_line, _right_line]
        _ids = ["t_a", "t_b"]

        # 2. Run test.
        _vertices = nu.vertices_from_lines(_lines, _ids)

        # 3. Verify final expectations.
        assert isinstance(_vertices, dict)
        assert list(_vertices.keys()) == _ids


class TestSplitLineWithPoints:
    @pytest.mark.skip(reason="TODO: Needs rework on the input data.")
    def test_with_valid_values(self):
        # 1. Define test data.
        _line = LineString([[0, 0], [1, 0], [2, 0], [5, 5]])
        _data = {"col1": ["name1"], "geometry": [_line]}
        _test_gdf = gpd.GeoDataFrame(_data, crs="EPSG:4326")
        _points = list(map(Point, [[1, 0], [2, 5]]))

        # 2. Run test.
        _result = nu.split_line_with_points(_test_gdf, _points)

        # 3. Verify expectations.
        assert _result


class TestCut:
    @pytest.mark.parametrize(
        "distance",
        [
            pytest.param(-math.inf, id="Negative infinite"),
            pytest.param(math.inf, id="Positive infinite"),
        ],
    )
    def test_with_invalid_distance(self, distance):
        # 1. Define test data.
        _line = LineString([[0, 0], [1, 0], [2, 0]])

        # 2. Run test.
        _left_line, _right_line = nu.cut(_line, distance)

        # 3. Verify expectations.
        assert _left_line is None
        assert _right_line == LineString(_line)

    def test_with_linestring(self):
        # 1. Define test data.
        _line = LineString([[0, 0], [1, 0], [2, 0]])
        _distance = 1.0
        # 2. Run test.
        _left_line, _right_line = nu.cut(_line, _distance)

        # 3. Verify expectations.
        assert _left_line == LineString([[0, 0], [1, 0]])
        assert _right_line == LineString([[1, 0], [2, 0]])

    def test_with_multilinestring(self):
        # 1. Define test data.
        _line = MultiLineString([[[0, 0], [1, 0], [2, 0]]])
        _distance = 1.0
        # 2. Run test.
        _left_line, _right_line = nu.cut(_line, _distance)

        # 3. Verify expectations.
        assert _left_line == LineString([[0, 0], [1, 0]])
        assert _right_line == LineString([[1, 0], [2, 0]])


class TestJoinNodesEdges:
    @pytest.mark.skip(reason="TODO: Test data should improve, node_fid missing")
    @pytest.mark.parametrize(
        "id_name", [pytest.param("col1_left"), pytest.param("col1_right")]
    )
    def test_with_valid_data(self, id_name: str):
        # 1. Define test data.
        _edges_data = {
            "col1": ["first_edge", "second_edge"],
            "geometry": [
                LineString([[0, 0], [2, 0]]),
                LineString([[2, 0], [3, 0]]),
            ],
        }
        _edges = gpd.GeoDataFrame(_edges_data, crs="EPSG:4326")
        _nodes_data = {
            "col1": ["first_node", "second_node"],
            "geometry": [
                Point([0, 0]),
                Point([2, 0]),
            ],
        }
        _nodes = gpd.GeoDataFrame(_nodes_data, crs="EPSG:4326")

        # 2. Run test.
        _node_gdf = nu.join_nodes_edges(_nodes, _edges, id_name)

        # 3. Verify final expectations.
        assert isinstance(_node_gdf, gpd.GeoDataFrame)


class TestDeleteDuplicates:
    def test_with_valid_data(self):
        _base_coords = [[0.42, 0.42], [4.2, 4.2], [42, 42]]
        _diff = 1e-09
        _almost_equal = [[x + _diff, y + _diff] for x, y in _base_coords]
        _list_coords = []
        _list_coords.extend(_base_coords)
        _list_coords.extend(_almost_equal)
        _points = list(map(Point, _list_coords))
        assert len(_points) == 6

        # 2. Run test
        _unique_points = nu.delete_duplicates(_points)

        # 3. Verify exepctations.
        assert len(_unique_points) == 3

        for _point in _unique_points:
            assert any(_point.almost_equals(_p) for _p in _points[:3])
