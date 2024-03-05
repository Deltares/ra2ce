import numpy as np

from ra2ce.graph.origins_destinations import closest_node


class TestOriginsDestinations:
    def test_closest_node(self):
        # 1. Define test.
        _left_array = np.array([0, 1, 2, 3])
        _right_array = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])

        # 2. Run test.
        _result = closest_node(_left_array, _right_array)

        # 3. Verify final expectations.
        assert len(_result) == 4
        assert list(_result) == [0, 1, 2, 3]
