import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.indirect_analysis_runner import IndirectAnalysisRunner
from tests.runners.dummy_classes import DummyRa2ceInput


class TestIndirectAnalysisRunner:
    def test_init_direct_analysis_runner(self):
        _runner = IndirectAnalysisRunner()
        assert str(_runner) == "Indirect Analysis Runner"

    @pytest.fixture
    def dummy_ra2ce_input(self):
        _ra2ce_input = DummyRa2ceInput()
        assert isinstance(_ra2ce_input, ConfigWrapper)
        yield _ra2ce_input

    def test_given_indirect_configuration_can_run(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        dummy_ra2ce_input.analysis_config.config_data.analyses = [
            AnalysisSectionLosses(analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY)
        ]

        # 2. Run test.
        _result = IndirectAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert _result

    def test_given_wrong_analysis_configuration_cannot_run(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.

        # 2. Run test.
        _result = IndirectAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert not _result
