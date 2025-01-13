from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.runners.losses_analysis_runner import LossesAnalysisRunner


class TestLossesAnalysisRunner:
    def test_init_losses_analysis_runner(self):
        _runner = LossesAnalysisRunner()
        assert str(_runner) == "Losses Analysis Runner"

    def test_given_losses_configuration_can_run(
        self, valid_analysis_collection: AnalysisCollection
    ):
        # 1. Define test data.
        _losses_analysis = valid_analysis_collection.get_analysis(
            AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY
        )

        # 2. Run test.
        _result = LossesAnalysisRunner().can_run(
            _losses_analysis,
            valid_analysis_collection,
        )

        # 3. Verify expectations.
        assert _result is True

    def test_given_wrong_analysis_configuration_cannot_run(
        self, dummy_analysis_collection: AnalysisCollection
    ):
        # 1. Define test data.
        _losses_analysis = dummy_analysis_collection.get_analysis(
            AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY
        )
        assert _losses_analysis is None

        # 2. Run test.
        _result = LossesAnalysisRunner().can_run(
            _losses_analysis, dummy_analysis_collection
        )

        # 3. Verify expectations.
        assert _result is False
