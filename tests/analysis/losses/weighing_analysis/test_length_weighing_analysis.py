import numpy as np
import pytest

from ra2ce.analysis.losses.weighing_analysis.length_weighing_analysis import (
    LengthWeighingAnalysis,
)
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class TestLengthWeighingAnalysis:
    def test_init(self):
        # 1. Define test data.
        _analysis = LengthWeighingAnalysis()

        # 2. Verify expectations.
        assert isinstance(_analysis, LengthWeighingAnalysis)
        assert isinstance(_analysis, WeighingAnalysisProtocol)

    @pytest.fixture
    def valid_analysis(self) -> LengthWeighingAnalysis:
        return LengthWeighingAnalysis()

    def test_calculate_distance(self, valid_analysis: LengthWeighingAnalysis):
        # 1. Run test
        _calculated_distance = valid_analysis.get_current_value()

        # 2. Verify expectations.
        assert np.isnan(_calculated_distance)

    def test_calculate_alternative_distance(
        self, valid_analysis: LengthWeighingAnalysis
    ):
        # 1. Define test data.
        _alt_distance = 42

        # 1. Run test
        _calculated_distance = valid_analysis.calculate_alternative_value(_alt_distance)

        # 2. Verify expectations.
        assert _calculated_distance == _alt_distance

    def test_extend_graph(self, valid_analysis: LengthWeighingAnalysis):
        # 1. Define test data.
        _graph_dict = dict(my_value=42)

        # 2. Run test.
        valid_analysis.extend_graph(_graph_dict)

        # 3. Verify expectations
        assert len(_graph_dict) == 1
        assert _graph_dict["my_value"] == 42
