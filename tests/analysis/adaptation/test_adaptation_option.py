import pytest

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from tests.analysis.adaptation.conftest import AdaptationOptionCases


class TestAdaptationOption:
    @pytest.mark.parametrize(
        "losses_analysis",
        [AnalysisLossesEnum.SINGLE_LINK_LOSSES, AnalysisLossesEnum.MULTI_LINK_LOSSES],
    )
    def test_from_config(
        self,
        valid_adaptation_config: AnalysisConfigWrapper,
        losses_analysis: AnalysisLossesEnum,
    ):
        # 1. Define test data.
        _orig_path = valid_adaptation_config.config_data.input_path
        _expected_path = _orig_path.parent.joinpath(
            valid_adaptation_config.config_data.adaptation.adaptation_options[0].id,
            "losses",
            "input",
        )

        valid_adaptation_config.config_data.adaptation.losses_analysis = losses_analysis

        # 2. Run test.
        _option = AdaptationOption.from_config(
            analysis_config=valid_adaptation_config,
            adaptation_option=valid_adaptation_config.config_data.adaptation.adaptation_options[
                0
            ],
        )

        # 3. Verify expectations.
        assert isinstance(_option, AdaptationOption)
        assert _option.id == "AO0"
        assert _option.damages_input.analysis.analysis == AnalysisDamagesEnum.DAMAGES
        assert _option.losses_input.analysis.analysis == losses_analysis
        assert _option.losses_input.input_path == _expected_path

    def test_from_config_no_damages_losses_raises(self):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        with pytest.raises(ValueError) as _exc:
            AdaptationOption.from_config(
                analysis_config=_config,
                adaptation_option=AnalysisSectionAdaptation(),
            )

        # 3. Verify expectations.
        assert _exc.match(
            "Damages and losses sections are required to create an adaptation option."
        )

    @pytest.mark.parametrize(
        "adaptation_option",
        AdaptationOptionCases.cases,
    )
    def test_calculate_option_cost(
        self,
        valid_adaptation_config: AnalysisConfigWrapper,
        adaptation_option: tuple[AnalysisSectionAdaptation, float],
    ):
        # 1. Define test data.
        _option = AdaptationOption.from_config(
            analysis_config=valid_adaptation_config,
            adaptation_option=adaptation_option[0],
        )
        _time_horizon = valid_adaptation_config.config_data.adaptation.time_horizon
        _discount_rate = valid_adaptation_config.config_data.adaptation.discount_rate

        # 2. Run test.
        _cost = _option.calculate_cost(_time_horizon, _discount_rate)

        # 3. Verify expectations.
        assert _cost == pytest.approx(adaptation_option[1])
