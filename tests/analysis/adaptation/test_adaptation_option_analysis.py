import pytest

from ra2ce.analysis.adaptation.adaptation_option_analysis import (
    AdaptationOptionAnalysis,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.damages.damages import Damages
from ra2ce.analysis.losses.losses_base import LossesBase
from ra2ce.analysis.losses.multi_link_losses import MultiLinkLosses
from ra2ce.analysis.losses.single_link_losses import SingleLinkLosses


class TestAnalysisOptionAnalysis:
    @pytest.mark.parametrize(
        "analysis_type, expected_analysis",
        [
            (AnalysisDamagesEnum.DAMAGES, Damages),
            (AnalysisLossesEnum.SINGLE_LINK_LOSSES, SingleLinkLosses),
            (AnalysisLossesEnum.MULTI_LINK_LOSSES, MultiLinkLosses),
        ],
    )
    def test_get_analysis_returns_tuple(
        self,
        analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum,
        expected_analysis: type[Damages | LossesBase],
    ):
        # 1./2. Define test data./Run test.
        _result = AdaptationOptionAnalysis.get_analysis(analysis_type)

        # 3. Verify expectations.
        assert isinstance(_result, tuple)
        assert _result[0] == expected_analysis
        assert isinstance(_result[1], str)

    def test_get_analysis_raises_not_implemented_error(self):
        # 1. Define test data.
        _analysis_type = "not implemented"

        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc:
            AdaptationOptionAnalysis.get_analysis(_analysis_type)

        # 3. Verify expectations.
        assert exc.match(f"Analysis {_analysis_type} not implemented")

    @pytest.mark.parametrize(
        "analysis_type, expected_analysis",
        [
            pytest.param(AnalysisDamagesEnum.DAMAGES, Damages, id="damages"),
            pytest.param(
                AnalysisLossesEnum.SINGLE_LINK_LOSSES,
                SingleLinkLosses,
                id="single_link_losses",
            ),
            pytest.param(
                AnalysisLossesEnum.MULTI_LINK_LOSSES,
                MultiLinkLosses,
                id="multi_link_losses",
            ),
        ],
    )
    def test_from_config_returns_object(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
        analysis_type: AnalysisLossesEnum,
        expected_analysis: type[Damages | LossesBase],
    ):
        # 1. Define test data.
        _analysis_config = valid_adaptation_config[1]
        assert _analysis_config.config_data.adaptation
        _orig_path = _analysis_config.config_data.input_path
        _expected_path = _orig_path.parent.joinpath(
            "input",
            _analysis_config.config_data.adaptation.adaptation_options[0].id,
            analysis_type.config_value,
            "input",
        )

        _analysis_config.config_data.adaptation.losses_analysis = analysis_type
        _id = _analysis_config.config_data.adaptation.adaptation_options[0].id

        # 2. Run test.
        _result = AdaptationOptionAnalysis.from_config(
            analysis_config=_analysis_config, analysis=analysis_type, option_id=_id
        )

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOptionAnalysis)
        assert _result.analysis_type == expected_analysis
        assert _result.analysis_input.input_path == _expected_path
