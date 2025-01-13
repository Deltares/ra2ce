from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.runners.damages_analysis_runner import DamagesAnalysisRunner


class TestDamagesAnalysisRunner:
    def test_init_damages_analysis_runner(self):
        _runner = DamagesAnalysisRunner()
        assert str(_runner) == "Damages Analysis Runner"

    def test_given_damages_configuration_can_run(
        self, damages_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        _analysis_collection = AnalysisCollection.from_config(
            damages_ra2ce_input.analysis_config
        )
        assert _analysis_collection.get_analysis(AnalysisDamagesEnum.DAMAGES)
        _analysis_collection.damages_analyses[0].graph_file_hazard = GraphFile(
            graph=GeoDataFrame()
        )

        # 2. Run test.
        _result = DamagesAnalysisRunner().can_run(
            _analysis_collection.get_analysis(AnalysisDamagesEnum.DAMAGES),
            _analysis_collection,
        )

        # 3. Verify expectations.
        assert _result is True

    def test_given_wrong_analysis_configuration_cannot_run(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        _analysis_collection = AnalysisCollection.from_config(
            dummy_ra2ce_input.analysis_config
        )
        assert _analysis_collection.get_analysis(AnalysisDamagesEnum.DAMAGES) is None

        # 2. Run test.
        _result = DamagesAnalysisRunner().can_run(
            _analysis_collection.get_analysis(AnalysisDamagesEnum.DAMAGES),
            _analysis_collection,
        )

        # 3. Verify expectations.
        assert _result is False

    def test_given_wrong_network_hazard_configuration_cannot_run(
        self, damages_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        _analysis_collection = AnalysisCollection.from_config(
            damages_ra2ce_input.analysis_config
        )
        assert _analysis_collection.get_analysis(AnalysisDamagesEnum.DAMAGES)
        _analysis_collection.damages_analyses[0].graph_file_hazard = GraphFile(
            graph="wrong_input"
        )

        # 2. Run test.
        _result = DamagesAnalysisRunner().can_run(
            _analysis_collection.get_analysis(AnalysisDamagesEnum.DAMAGES),
            _analysis_collection,
        )

        # 3. Verify expectations.
        assert _result is False
