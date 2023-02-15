from ra2ce.runners.direct_analysis_runner import DirectAnalysisRunner
from tests.runners.dummy_classes import DummyRa2ceInput


class TestDirectAnalysisRunner:
    def test_init_direct_analysis_runner(self):
        _runner = DirectAnalysisRunner()
        assert str(_runner) == "Direct Analysis Runner"

    def test_given_direct_configuration_can_run(self):
        # 1. Define test data.
        _input_config = DummyRa2ceInput()
        assert _input_config
        _input_config.analysis_config.config_data["direct"] = None
        _input_config.network_config.config_data["hazard"] = dict(hazard_map="A value")

        # 2. Run test.
        _result = DirectAnalysisRunner.can_run(_input_config)

        # 3. Verify expectations.
        assert _result

    def test_given_wrong_analysis_configuration_cannot_run(self):
        # 1. Define test data.
        _input_config = DummyRa2ceInput()
        assert _input_config
        _input_config.network_config.config_data["hazard"] = dict(hazard_map="A value")

        # 2. Run test.
        _result = DirectAnalysisRunner.can_run(_input_config)

        # 3. Verify expectations.
        assert not _result

    def test_given_wrong_network_hazard_configuration_cannot_run(self):
        # 1. Define test data.
        _input_config = DummyRa2ceInput()
        assert _input_config
        _input_config.analysis_config.config_data["direct"] = None

        # 2. Run test.
        _result = DirectAnalysisRunner.can_run(_input_config)

        # 3. Verify expectations.
        assert not _result

    def test_given_no_network_config_returns_false(self):
        # 1. Define test data.
        _input_config = DummyRa2ceInput()
        assert _input_config
        _input_config.analysis_config.config_data["direct"] = "sth"
        _input_config.network_config = None

        # 2. Run test.
        _result = DirectAnalysisRunner.can_run(_input_config)

        # 3. Verify expectations.
        assert not _result
