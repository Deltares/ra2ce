import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDamages,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.direct_analysis_runner import DirectAnalysisRunner
from tests.runners.dummy_classes import DummyRa2ceInput


class TestDirectAnalysisRunner:
    def test_init_direct_analysis_runner(self):
        _runner = DirectAnalysisRunner()
        assert str(_runner) == "Direct Analysis Runner"

    @pytest.fixture
    def dummy_ra2ce_input(self):
        _ra2ce_input = DummyRa2ceInput()
        assert isinstance(_ra2ce_input, ConfigWrapper)
        yield _ra2ce_input

    def test_given_direct_configuration_can_run(self, dummy_ra2ce_input: ConfigWrapper):
        # 1. Define test data.
        dummy_ra2ce_input.analysis_config.config_data.analyses = [
            AnalysisSectionDamages(analysis=AnalysisDamagesEnum.EFFECTIVENESS_MEASURES)
        ]
        dummy_ra2ce_input.network_config.config_data.hazard.hazard_map = "A value"

        # 2. Run test.
        _result = DirectAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert _result

    def test_given_wrong_analysis_configuration_cannot_run(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        dummy_ra2ce_input.network_config.config_data.hazard.hazard_map = "A value"

        # 2. Run test.
        _result = DirectAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert not _result

    def test_given_wrong_network_hazard_configuration_cannot_run(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        dummy_ra2ce_input.analysis_config.config_data.analyses = [
            AnalysisSectionDamages(analysis=AnalysisDamagesEnum.EFFECTIVENESS_MEASURES)
        ]

        # 2. Run test.
        _result = DirectAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert not _result

    def test_given_no_network_config_returns_false(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        dummy_ra2ce_input.analysis_config.config_data.analyses = [
            AnalysisSectionDamages(analysis=AnalysisDamagesEnum.EFFECTIVENESS_MEASURES)
        ]
        dummy_ra2ce_input.network_config = None

        # 2. Run test.
        _result = DirectAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert not _result
