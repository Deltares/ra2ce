import numpy as np
import pytest

from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.losses.weighing_analysis.length_weighing_analysis import (
    LengthWeighingAnalysis,
)
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class TestLengthWeighingAnalysis:
    def test_init(self):
        # 1. Define test data.
        _analysis = LengthWeighingAnalysis(None)

        # 2. Verify expectations.
        assert isinstance(_analysis, LengthWeighingAnalysis)
        assert isinstance(_analysis, WeighingAnalysisProtocol)

    @pytest.fixture
    def valid_analysis(self) -> LengthWeighingAnalysis:
        _analysis = LengthWeighingAnalysis(None)
        _analysis.edge_data = {WeighingEnum.TIME.config_value: 1, "avgspeed": 0.42}
        return _analysis

    def test_calculate_distance(self, valid_analysis: LengthWeighingAnalysis):
        # 1. Define test data.
        _expected_distance = 420.0
        _time = valid_analysis.edge_data[WeighingEnum.TIME.config_value]

        # 2. Run test
        _calculated_distance = valid_analysis._calculate_distance(_time)

        # 3. Verify expectations.
        assert _calculated_distance == pytest.approx(_expected_distance)

    def test_get_current_value(self, valid_analysis: LengthWeighingAnalysis):
        # 1. Define test data.
        _expected_distance = 420.0
        _dist = valid_analysis.edge_data.get(WeighingEnum.LENGTH.config_value, 0)
        assert not _dist

        # 2. Run test
        _current_distance = valid_analysis.get_current_value()

        # 3. Verify expectations.
        assert _current_distance == pytest.approx(_expected_distance)
        assert valid_analysis.edge_data[
            WeighingEnum.LENGTH.config_value
        ] == pytest.approx(_expected_distance)

    def test_calculate_alternative_value(self, valid_analysis: LengthWeighingAnalysis):
        # 1. Define test data.
        _alt_distance = 42

        # 1. Run test
        _calculated_distance = valid_analysis.calculate_alternative_value(_alt_distance)

        # 2. Verify expectations.
        assert _calculated_distance == _alt_distance
