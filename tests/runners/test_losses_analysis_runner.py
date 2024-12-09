import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.losses_analysis_runner import LossesAnalysisRunner


class TestLossesAnalysisRunner:
    def test_init_losses_analysis_runner(self):
        _runner = LossesAnalysisRunner()
        assert str(_runner) == "Losses Analysis Runner"

    def test_given_losses_configuration_can_run(self, dummy_ra2ce_input: ConfigWrapper):
        # 1. Define test data.
        dummy_ra2ce_input.analysis_config.config_data.analyses = [
            AnalysisSectionLosses(analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY)
        ]

        # 2. Run test.
        _result = LossesAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert _result

    def test_given_wrong_analysis_configuration_cannot_run(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.

        # 2. Run test.
        _result = LossesAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert not _result
