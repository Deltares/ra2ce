from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.indirect.origin_closest_destination import OriginClosestDestination
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.network_config_data.network_config_data import (
    NetworkSection,
    OriginsDestinationsSection,
)


class TestOriginClosestDestination:
    def test_init_with_category(self):
        # 1. Define test data.
        _config_dict = AnalysisConfigData(
            origins_destinations=OriginsDestinationsSection(
                origins_names="",
                destinations_names="",
                id_name_origin_destination="",
                origin_out_fraction="",
                origin_count="",
                category="dummy_value",
            ),
            network=NetworkSection(file_id=""),
        )
        _analysis = AnalysisSectionIndirect(threshold="", weighing=WeighingEnum.INVALID)
        _graph_files = GraphFilesCollection()
        _hazard_names = None

        # 2. Run test.
        _ocd = OriginClosestDestination(
            file_id=_config_dict.network.file_id,
            origins_destinations=_config_dict.origins_destinations,
            analysis=_analysis,
            graph_file=_graph_files.origins_destinations_graph,
            graph_file_hazard=_graph_files.origins_destinations_graph_hazard,
            static_path=_config_dict.static_path,
            hazard_names=_hazard_names,
        )

        # 3. Verify expectations.
        assert isinstance(_ocd, OriginClosestDestination)
        assert isinstance(_ocd.analysis, AnalysisSectionIndirect)
        assert _ocd.analysis == _analysis
        assert _ocd.hazard_names == _hazard_names
        assert _ocd.results_dict == {}
        assert _ocd.destination_key_value == "dummy_value"
