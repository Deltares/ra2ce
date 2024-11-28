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


class TestAdaptationOption:
    def test_from_config(self, valid_adaptation_config: AnalysisConfigData):
        # 1. Define test data.

        # 2. Run test.
        _option = AdaptationOption.from_config(
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

        # TODO: test adding the adaptation id to the paths

    def test_from_config_no_damages_losses_raises(self):
        # 1. Define test data.
        _config = AnalysisConfigData()

        # 2. Run test.
        with pytest.raises(ValueError) as _exc:
            AdaptationOption.from_config(
                adaptation_option=AnalysisSectionAdaptation(),
                damages_section=None,
                losses_section=None,
            )

        # 3. Verify expectations.
        assert _exc.match(
            "Damages and losses sections are required to create an adaptation option."
        )
