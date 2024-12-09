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
        dummy_ra2ce_input.network_config.config_data.hazard.hazard_map = "A value"

        # 2. Run test.
        _result = AdaptationAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert not _result
