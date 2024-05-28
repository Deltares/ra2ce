import pytest

from ra2ce.analysis.losses.traffic_analysis.traffic_analysis_base import (
    TrafficAnalysisBase,
)


class TestTrafficAnalysisBase:
    def test_initialize_traffic_analysis_base(self):
        """
        This test verifies that `TrafficAnalysisBase` is (and will be) an abstract class (`abc.ABC`).
        """
        with pytest.raises(TypeError) as exc_err:
            TrafficAnalysisBase()

        assert (
            str(exc_err.value)
            == "Can't instantiate abstract class TrafficAnalysisBase with abstract methods _get_accumulated_traffic_from_node, _get_route_traffic"
        )
