from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.runners.damages_analysis_runner import DamagesAnalysisRunner


class TestDamagesAnalysisRunner:
    def test_init_damages_analysis_runner(self):
        _runner = DamagesAnalysisRunner()
        assert str(_runner) == "Damages Analysis Runner"

    def test_given_damages_configuration_can_run(
        self, valid_analysis_collection: AnalysisCollection
    ):
        # 1. Define test data.
        _damages_analysis = valid_analysis_collection.get_analysis(
            AnalysisDamagesEnum.DAMAGES
        )
        assert _damages_analysis

        # 2. Run test.
        _result = DamagesAnalysisRunner().can_run(
            _damages_analysis, valid_analysis_collection
        )

        # 3. Verify expectations.
        assert _result is True

    def test_given_wrong_analysis_configuration_cannot_run(
        self, dummy_analysis_collection: AnalysisCollection
    ):
        # 1. Define test data.
        _damages_analysis = dummy_analysis_collection.get_analysis(
            AnalysisDamagesEnum.DAMAGES
        )
        assert _damages_analysis is None

        # 2. Run test.
        _result = DamagesAnalysisRunner().can_run(
            _damages_analysis, dummy_analysis_collection
        )

        # 3. Verify expectations.
        assert _result is False

    def test_given_wrong_network_hazard_configuration_cannot_run(
        self, valid_analysis_collection: AnalysisCollection
    ):
        # 1. Define test data.
        _damages_analysis = valid_analysis_collection.get_analysis(
            AnalysisDamagesEnum.DAMAGES
        )
        assert _damages_analysis
        _damages_analysis.graph_file_hazard = GraphFile(graph="wrong_input")

        # 2. Run test.
        _result = DamagesAnalysisRunner().can_run(
            _damages_analysis, valid_analysis_collection
        )

        # 3. Verify expectations.
        assert _result is False
