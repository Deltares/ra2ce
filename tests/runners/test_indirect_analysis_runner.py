from ra2ce.runners.indirect_analysis_runner import IndirectAnalysisRunner
from tests.runners.dummy_classes import DummyRa2ceInput


class TestIndirectAnalysisRunner:
    def test_init_direct_analysis_runner(self):
        _runner = IndirectAnalysisRunner()
        assert str(_runner) == "Indirect Analysis Runner"

    def test_given_direct_configuration_can_run(self):
        # 1. Define test data.
        _input_config = DummyRa2ceInput()
        assert _input_config
        _input_config.analysis_config.config_data["indirect"] = None

        # 2. Run test.
        _result = IndirectAnalysisRunner.can_run(_input_config)

        # 3. Verify expectations.
        assert _result

    def test_given_wrong_analysis_configuration_cannot_run(self):
        # 1. Define test data.
        _input_config = DummyRa2ceInput()
        assert _input_config

        # 2. Run test.
        _result = IndirectAnalysisRunner.can_run(_input_config)

        # 3. Verify expectations.
        assert not _result
