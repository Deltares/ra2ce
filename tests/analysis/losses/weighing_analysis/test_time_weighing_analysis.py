import pytest

from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.losses.weighing_analysis.time_weighing_analysis import (
    TimeWeighingAnalysis,
)
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class TestTimeWeighingAnalysis:
    def test_init(self):
        # 1. Define test data.
        _analysis = TimeWeighingAnalysis()

        # 2. Verify expectations.
        assert isinstance(_analysis, TimeWeighingAnalysis)
        assert isinstance(_analysis, WeighingAnalysisProtocol)

    @pytest.fixture
    def valid_analysis(self) -> TimeWeighingAnalysis:
        _analysis = TimeWeighingAnalysis()
        _analysis.edge_data = {WeighingEnum.LENGTH.config_value: 420, "avgspeed": 0.42}
        return _analysis

    def test_calculate_time(self, valid_analysis: TimeWeighingAnalysis):
        # 1. Define test data.
        _expected_time = 1.0
        _dist = valid_analysis.edge_data[WeighingEnum.LENGTH.config_value]

        # 2. Run test.
        _calculated_time = valid_analysis._calculate_time(_dist)

        # 3. Verify expectations.
        assert _calculated_time == pytest.approx(_expected_time)

    def test_get_current_value(self, valid_analysis: TimeWeighingAnalysis):
        # 1. Define test data.
        _expected_time = 1.0
        _time = valid_analysis.edge_data.get(WeighingEnum.TIME.config_value, 0)
        assert not _time

        # 2. Run test
        _current_time = valid_analysis.get_current_value()

        # 3. Verify expectations.
        assert _current_time == pytest.approx(_expected_time)
        assert valid_analysis.edge_data[
            WeighingEnum.TIME.config_value
        ] == pytest.approx(_expected_time)

    def test_calculate_alternative_value(self, valid_analysis: TimeWeighingAnalysis):
        # 1. Define test data.
        _alt_distance = 240
        _expected_time = 0.57

        # 2. Run test
        _calculated_time = valid_analysis.calculate_alternative_value(_alt_distance)

        # 3. Verify expectations.
        assert _calculated_time == pytest.approx(_expected_time, rel=1e-2)

    def test_extend_graph(self, valid_analysis: TimeWeighingAnalysis):
        # 1. Define test data.
        _graph_dict = dict(my_value=42)
        _time_list = [4.2]
        valid_analysis.time_list = _time_list

        # 2. Run test.
        valid_analysis.extend_graph(_graph_dict)

        # 3. Verify expectations
        assert len(_graph_dict) == 2
        assert _graph_dict["my_value"] == 42
        assert _graph_dict[WeighingEnum.TIME.config_value] == _time_list
