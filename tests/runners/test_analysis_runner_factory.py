from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.runners.analysis_runner_factory import AnalysisRunnerFactory
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class TestAnalysisRunnerFactory:
    def test_get_runner_without_input_raises_returns_empty_list(self):
        _analysis_collection = AnalysisCollection()
        _result = AnalysisRunnerFactory.get_supported_runners(_analysis_collection)

        assert isinstance(_result, list)
        assert len(_result) == 0

    def test_get_runner_with_many_supported_runners_returns_analysis_runner_instance(
        self, valid_analysis_collection: AnalysisCollection
    ):
        # 1. Run test.
        _supported_runners = AnalysisRunnerFactory.get_supported_runners(
            valid_analysis_collection
        )

        # 2. Verify final expectations.
        assert isinstance(_supported_runners, list)
        assert len(_supported_runners) == 3
        assert all(isinstance(_sr, AnalysisRunner) for _sr in _supported_runners)
