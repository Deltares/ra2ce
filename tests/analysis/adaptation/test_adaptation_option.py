import pytest

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionAdaptation,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from tests.analysis.adaptation.conftest import AdaptationOptionCases


class TestAdaptationOption:
    def test_from_config(self, valid_adaptation_config: AnalysisConfigData):
        # 1. Define test data.
        _orig_path = valid_adaptation_config.losses_list[0].resilience_curves_file
        _expected_path = _orig_path.parent.joinpath(
            "input",
            valid_adaptation_config.adaptation.adaptation_options[0].id,
            "losses",
            _orig_path.name,
        )

        # 2. Run test.
        _option = AdaptationOption.from_config(
            root_path=valid_adaptation_config.root_path,
            adaptation_option=valid_adaptation_config.adaptation.adaptation_options[0],
            damages_section=valid_adaptation_config.get_analysis(
                AnalysisDamagesEnum.DAMAGES
            ),
            losses_section=valid_adaptation_config.get_analysis(
                AnalysisLossesEnum.SINGLE_LINK_LOSSES
            ),
        )

        # 3. Verify expectations.
        assert isinstance(_option, AdaptationOption)
        assert _option.id == "AO0"
        assert _option.damages_config.analysis == AnalysisDamagesEnum.DAMAGES
        assert _option.losses_config.analysis == AnalysisLossesEnum.SINGLE_LINK_LOSSES
        assert _option.losses_config.resilience_curves_file == _expected_path

    def test_from_config_no_damages_losses_raises(self):
        # 1. Define test data.
        _config = AnalysisConfigData()

        # 2. Run test.
        with pytest.raises(ValueError) as _exc:
            AdaptationOption.from_config(
                root_path=_config.root_path,
                adaptation_option=AnalysisSectionAdaptation(),
                damages_section=None,
                losses_section=None,
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
        valid_adaptation_config: AnalysisConfigData,
        adaptation_option: tuple[AnalysisSectionAdaptation, float],
    ):
        # 1. Define test data.
        _option = AdaptationOption.from_config(
            root_path=valid_adaptation_config.root_path,
            adaptation_option=adaptation_option[0],
            damages_section=valid_adaptation_config.damages_list[0],
            losses_section=valid_adaptation_config.losses_list[0],
        )
        _time_horizon = valid_adaptation_config.adaptation.time_horizon
        _discount_rate = valid_adaptation_config.adaptation.discount_rate

        # 2. Run test.
        _cost = _option.calculate_cost(_time_horizon, _discount_rate)

        # 3. Verify expectations.
        assert _cost == pytest.approx(adaptation_option[1])
