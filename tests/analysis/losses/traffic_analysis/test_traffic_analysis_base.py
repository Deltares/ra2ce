import pytest

from ra2ce.analysis.losses.traffic_analysis.traffic_analysis_base import (
    TrafficAnalysisBase,
)


class TestTrafficAnalysisBase:
    def test_initialize_traffic_analysis_base(self):
        """
        This test verifies that `TrafficAnalysisBase` is (and will be) an abstract class (`abc.ABC`).
        """
        # 1. Define test data
        # Disclaimer: Done like this as in Python 3.11 the exception error differs slightly.
        _expected_class_str = f"Can't instantiate abstract class {TrafficAnalysisBase.__name__}"
        _expected_methods_str = "abstract methods"
        _expected_methods_list = [
            "_get_accumulated_traffic_from_node",
            "_get_route_traffic"
        ]

        # 2. Run test
        with pytest.raises(TypeError) as exc_err:
            TrafficAnalysisBase()

        # 3. Verify expectations
        _exception_mssg = str(exc_err.value)
        assert _expected_class_str in _exception_mssg
        assert _expected_methods_str in _exception_mssg
        for method in _expected_methods_list:
            assert method in _exception_mssg
