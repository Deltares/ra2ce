import math

import pytest
from shapely.geometry import LineString

from ra2ce.graph.segmentation import Segmentation


class TestSegmentation:
    def test_init(self):
        _segmentation = Segmentation(None, None, False)
        assert isinstance(_segmentation, Segmentation)

    @pytest.mark.parametrize(
        "distance",
        [
            pytest.param(-math.inf, id="Negative infinite"),
            pytest.param(math.inf, id="Positive infinite"),
        ],
    )
    def test_cut_with_wrong_distance(self, distance: float):
        # 1. Define test data.
        _segmentation = Segmentation(None, None, False)
        _line = LineString([[0, 0], [1, 0], [2, 0]])

        # 2. Run test.
        _result = _segmentation.cut(_line, distance)

        # 3. Verify final expectations.
        assert len(_result) == 1
        assert isinstance(_result[0], LineString)

    def test_cut_with_projected_line_equals_distance(self):
        # 1. Define test data.
        _segmentation = Segmentation(None, None, False)
        _line = LineString([[0, 0], [1, 0], [2, 0]])

        # 2. Run test.
        _result = _segmentation.cut(_line, _line.length / 2)

        # 3. Verify final expectations.
        assert len(_result) == 2
        assert all(isinstance(_r, LineString) for _r in _result)

    def test_cut_with_projected_line_greater_than_distance(self):
        # 1. Define test data.
        _segmentation = Segmentation(None, None, False)
        _line = LineString([[0, 0], [1, 1], [2, 2]])
        _distance = 1.0

        # 2. Run test.
        _result = _segmentation.cut(_line, _distance)

        # 3. Verify final expectations.
        assert len(_result) == 2
        assert all(isinstance(_r, LineString) for _r in _result)

    def test_check_divisibility_is_true(self):
        # 1. Define test data.
        _segmentation = Segmentation(None, None, False)
        # 2. Run test.
        assert _segmentation.check_divisibility(4, 2)

    def test_check_divisibility_is_false(self):
        # 1. Define test data.
        _segmentation = Segmentation(None, None, False)
        # 2. Run test.
        assert not _segmentation.check_divisibility(2, 4)

    @pytest.mark.parametrize("length, segments", [(1, 2), (3, 1)])
    def test_number_of_segments(self, length: float, segments: float):
        # 1. Define test data.
        _segmentation = Segmentation(None, None, False)
        _line = LineString([[0, 0], [1, 0], [2, 0]])

        # 2. Run test.
        _return_value = _segmentation.number_of_segments(_line, length)

        # 3. Verify expectations
        assert _return_value == segments

    def test_split_linestring_nsegments_is_one(self):
        # 1. Define test data.
        _segmentation = Segmentation(None, None, False)
        _line = LineString([[0, 0], [1, 0], [2, 0]])
        _length = 2

        # 2. Run test.
        _return_value = _segmentation.split_linestring(_line, _length)

        # 3. Verify expectations
        assert _return_value == [_line]
