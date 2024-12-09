from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
    AnalysisSectionAdaptationOption,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.adaptation_analysis_runner import AdaptationAnalysisRunner


class TestAdaptationAnalysisRunner:
    def test_init_adaptation_analysis_runner(self):
        _runner = AdaptationAnalysisRunner()
        assert str(_runner) == "Adaptation Analysis Runner"

    def test_given_wrong_analysis_configuration_cannot_run(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        assert dummy_ra2ce_input.analysis_config.config_data.adaptation is None

        # 2. Run test.
        _result = AdaptationAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert not _result

    def test_given_valid_damages_input_configuration_cannot_run(
        self, damages_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        assert damages_ra2ce_input.analysis_config.config_data.adaptation is None

        # 2. Run test.
        _result = AdaptationAnalysisRunner.can_run(damages_ra2ce_input)

        # 3. Verify expectation
        assert _result is False

    def test_given_valid_damages_and_adaptation_input_configuration_can_run(
        self, damages_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        assert damages_ra2ce_input.analysis_config.config_data.adaptation is None
        _adaptation_config = AnalysisSectionAdaptation()
        _adaptation_config.adaptation_options = [
            AnalysisSectionAdaptationOption(id="AO0"),
            AnalysisSectionAdaptationOption(id="AO1"),
            AnalysisSectionAdaptationOption(id="AO2"),
        ]
        damages_ra2ce_input.analysis_config.config_data.analyses.append(
            _adaptation_config
        )

        # 2. Run test.
        _result = AdaptationAnalysisRunner.can_run(damages_ra2ce_input)

        # 3. Verify expectation
        assert _result is True
