from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionIndirect,
)
from ra2ce.analyses.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analyses.indirect.origin_closest_destination import OriginClosestDestination
from ra2ce.graph.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.graph.network_config_data.network_config_data import (
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
            config=_config_dict,
            analysis=_analysis,
            graph_files=_graph_files,
            hazard_names_df=_hazard_names,
        )

        # 3. Verify expectations.
        assert isinstance(_ocd, OriginClosestDestination)
        assert _ocd.analysis == _analysis
        assert _ocd.config == _config_dict
        assert _ocd.hazard_names == _hazard_names
        assert _ocd.results_dict == {}
        assert _ocd.destination_key_value == "dummy_value"
