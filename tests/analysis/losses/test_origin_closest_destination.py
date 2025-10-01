from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.losses.origin_closest_destination import OriginClosestDestination
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.network_config_data.network_config_data import (
    NetworkSection,
    OriginsDestinationsSection,
)


class TestOriginClosestDestination:
    def test_init_with_category(self):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()
        _config.config_data = AnalysisConfigData(
            origins_destinations=OriginsDestinationsSection(
                origins_names="",
                destinations_names="",
                origin_out_fraction="",
                origin_count="",
                category="dummy_value",
            ),
            network=NetworkSection(file_id=""),
        )
        _analysis = AnalysisSectionLosses(threshold="", weighing=WeighingEnum.INVALID)
        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=_analysis,
            analysis_config=_config,
            graph_file_hazard=GraphFilesCollection().base_network_hazard,
        )

        # 2. Run test.
        _ocd = OriginClosestDestination(_analysis_input)

        # 3. Verify expectations.
        assert isinstance(_ocd, OriginClosestDestination)
        assert isinstance(_ocd.analysis, AnalysisSectionLosses)
        assert _ocd.analysis == _analysis
        assert _ocd.results_dict == {}
        assert _ocd.destination_key_value == "dummy_value"
