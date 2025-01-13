from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionAdaptation,
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_enum import AnalysisEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.runners.analysis_runner_factory import AnalysisRunnerFactory
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class TestAnalysisRunnerFactory:
    def test_get_runner_without_input_raises_returns_empty_list(self):
        _analysis_collection = []
        _result = AnalysisRunnerFactory.get_supported_runners(_analysis_collection)

        assert isinstance(_result, list)
        assert len(_result) == 0

    def test_get_runner_with_many_supported_runners_returns_analysis_runner_instance(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        dummy_ra2ce_input.analysis_config.config_data = AnalysisConfigData(
            analyses=[
                AnalysisSectionDamages(analysis=AnalysisDamagesEnum.DAMAGES),
                AnalysisSectionLosses(
                    analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY
                ),
                AnalysisSectionAdaptation(analysis=AnalysisEnum.ADAPTATION),
            ],
        )
        _analysis_collection = AnalysisCollection.from_config(
            dummy_ra2ce_input.analysis_config
        )
        _analysis_collection.damages_analyses[0].graph_file_hazard = GraphFile(
            graph=GeoDataFrame()
        )

        # 2. Run test.
        _supported_runners = AnalysisRunnerFactory.get_supported_runners(
            _analysis_collection
        )

        # 3. Verify final expectations.
        assert isinstance(_supported_runners, list)
        assert len(_supported_runners) == 3
        assert all(isinstance(_sr, AnalysisRunner) for _sr in _supported_runners)

    def test_get_runner_with_many_losses_analyses_returns_single_runner_instance(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        dummy_ra2ce_input.analysis_config.config_data = AnalysisConfigData(
            analyses=[
                AnalysisSectionLosses(analysis=AnalysisLossesEnum.SINGLE_LINK_LOSSES),
                AnalysisSectionLosses(analysis=AnalysisLossesEnum.MULTI_LINK_LOSSES),
            ],
        )
        _analysis_collection = AnalysisCollection.from_config(
            dummy_ra2ce_input.analysis_config
        )

        # 2. Run test.
        _supported_runners = AnalysisRunnerFactory.get_supported_runners(
            _analysis_collection
        )

        # 3. Verify final expectations.
        assert isinstance(_supported_runners, list)
        assert len(_supported_runners) == 1
        assert isinstance(_supported_runners[0], AnalysisRunner)
