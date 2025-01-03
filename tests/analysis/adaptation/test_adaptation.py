import pytest

from ra2ce.analysis.adaptation.adaptation import Adaptation
from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from tests.analysis.adaptation.conftest import AdaptationOptionCases


class TestAdaptation:
    def test_initialize(
        self,
        valid_adaptation_config_with_input: tuple[
            AnalysisInputWrapper, AnalysisConfigWrapper
        ],
    ):
        # 1./2. Define test data./Run test.
        _adaptation = Adaptation(
            valid_adaptation_config_with_input[0], valid_adaptation_config_with_input[1]
        )

        # 3. Verify expectations.
        assert isinstance(_adaptation, Adaptation)
        assert isinstance(_adaptation, AnalysisBase)

    def test_execute_returns_result(
        self,
        valid_adaptation_config_with_input: tuple[
            AnalysisInputWrapper, AnalysisConfigWrapper
        ],
    ):
        # 1. Define test data.
        _adaptation = Adaptation(
            valid_adaptation_config_with_input[0], valid_adaptation_config_with_input[1]
        )

        # 2. Run test.
        _result = _adaptation.execute()

        # 3. Verify expectations.
        assert isinstance(_result, AnalysisResultWrapper)
        assert len(_result.results_collection) == 1
        _analysis_result = _result.results_collection[0].analysis_result
        assert not _analysis_result.geometry.empty
        assert all(
            [
                f"{_option.id}_bc_ratio" in _analysis_result.columns
                for _option in _adaptation.adaptation_options
            ]
        )
        for _option, _expected in AdaptationOptionCases.cases[1:]:
            assert _analysis_result[f"{_option.id}_bc_ratio"].sum(
                axis=0
            ) == pytest.approx(_expected[2])
