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
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.damages.damages import Damages
from ra2ce.analysis.losses.multi_link_losses import MultiLinkLosses
from ra2ce.analysis.losses.single_link_losses import SingleLinkLosses
from tests.analysis.adaptation.conftest import AdaptationOptionCases


class TestAdaptationOption:
    @pytest.mark.parametrize(
        "losses_analysis_type, losses_analysis",
        [
            (AnalysisLossesEnum.SINGLE_LINK_LOSSES, SingleLinkLosses),
            (AnalysisLossesEnum.MULTI_LINK_LOSSES, MultiLinkLosses),
        ],
    )
    def test_from_config(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
        losses_analysis_type: AnalysisLossesEnum,
        losses_analysis: type[SingleLinkLosses | MultiLinkLosses],
    ):
        # 1. Define test data.
        _orig_path = valid_adaptation_config[1].config_data.input_path
        _expected_path = _orig_path.parent.joinpath(
            "input",
            valid_adaptation_config[1].config_data.adaptation.adaptation_options[0].id,
            losses_analysis_type.config_value,
            "input",
        )

        valid_adaptation_config[
            1
        ].config_data.adaptation.losses_analysis = losses_analysis_type

        # 2. Run test.
        _option = AdaptationOption.from_config(
            analysis_config=valid_adaptation_config[1],
            adaptation_option=valid_adaptation_config[
                1
            ].config_data.adaptation.adaptation_options[0],
        )

        # 3. Verify expectations.
        assert isinstance(_option, AdaptationOption)
        assert _option.id == "AO0"
        assert len(_option.analyses) == 2
        assert Damages in [x.analysis_type for x in _option.analyses]
        assert losses_analysis in [x.analysis_type for x in _option.analyses]
        assert _expected_path in [x.analysis_input.input_path for x in _option.analyses]

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
    def test_calculate_option_cost_returns_float(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
        adaptation_option: tuple[AnalysisSectionAdaptation, float, float],
    ):
        # 1. Define test data.
        _option = AdaptationOption.from_config(
            analysis_config=valid_adaptation_config[1],
            adaptation_option=adaptation_option[0],
        )
        _time_horizon = valid_adaptation_config[1].config_data.adaptation.time_horizon
        _discount_rate = valid_adaptation_config[1].config_data.adaptation.discount_rate

        # 2. Run test.
        _cost = _option.calculate_cost(_time_horizon, _discount_rate)

        # 3. Verify expectations.
        assert isinstance(_cost, float)
        assert _cost == pytest.approx(adaptation_option[1])
