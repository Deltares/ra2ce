from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.origin_closest_destination import OriginClosestDestination
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.network_config_data import (
    OriginsDestinationsSection,
)
from ra2ce.network.networks_utils import get_nodes_and_edges_from_origin_graph


class MultiLinkOriginClosestDestination(AnalysisBase, AnalysisLossesProtocol):
    analysis: AnalysisSectionLosses
    graph_file: GraphFile
    graph_file_hazard: GraphFile
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames
    origins_destinations: OriginsDestinationsSection
    file_id: str
    _analysis_input: AnalysisInputWrapper

    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
    ) -> None:
        self.analysis = analysis_input.analysis
        self.graph_file = analysis_input.graph_file
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.static_path = analysis_input.static_path
        self.output_path = analysis_input.output_path
        self.hazard_names = analysis_input.hazard_names
        self.origins_destinations = analysis_input.origins_destinations
        self.file_id = analysis_input.file_id
        self._analysis_input = analysis_input

    def execute(self) -> AnalysisResultWrapper:
        _output_path = self.output_path.joinpath(self.analysis.analysis.config_value)

        analyzer = OriginClosestDestination(self._analysis_input)
        if self.analysis.calculate_route_without_disruption:
            (
                _base_graph,
                opt_routes_without_hazard,
                destinations,
            ) = analyzer.optimal_route_origin_closest_destination()

            if self.graph_file_hazard.file is None:
                origins = analyzer.load_origins()
                opt_routes_with_hazard = GeoDataFrame(data=None)
            else:
                (
                    _base_graph,
                    origins,
                    destinations,
                    agg_results,
                    opt_routes_with_hazard,
                ) = analyzer.multi_link_origin_closest_destination()

                (
                    opt_routes_with_hazard
                ) = analyzer.difference_length_with_without_hazard(
                    opt_routes_with_hazard, opt_routes_without_hazard
                )
        else:
            (
                _base_graph,
                origins,
                destinations,
                agg_results,
                opt_routes_with_hazard,
            ) = analyzer.multi_link_origin_closest_destination()
            opt_routes_without_hazard = GeoDataFrame()

        _nodes_graph, _edges_graph = get_nodes_and_edges_from_origin_graph(_base_graph)
        _base_name = self.analysis.name.replace(" ", "_")
        _analysis_result_wrapper = AnalysisResultWrapper(
            results_collection=[
                self._get_analysis_result(origins, _base_name + "_origins"),
                self._get_analysis_result(destinations, _base_name + "_destinations"),
                self._get_analysis_result(_nodes_graph, _base_name + "_results_nodes"),
                self._get_analysis_result(_edges_graph, _base_name + "_results_edges"),
                self._get_analysis_result(
                    opt_routes_without_hazard,
                    _base_name + "_optimal_routes_without_hazard",
                ),
                self._get_analysis_result(
                    opt_routes_with_hazard, _base_name + "_optimal_routes_with_hazard"
                ),
            ]
        )

        # Legacy code, previously only done to export to CSV.
        _opt_routes_name = _base_name + "_optimal_routes"
        if not opt_routes_without_hazard.empty:
            _analysis_result_wrapper.results_collection.append(
                self._get_analysis_result(opt_routes_with_hazard, _opt_routes_name)
            )
        if not opt_routes_with_hazard.empty:
            _analysis_result_wrapper.results_collection.append(
                self._get_analysis_result(opt_routes_without_hazard, _opt_routes_name)
            )

        if self.graph_file_hazard.file is not None:
            agg_results.to_excel(
                _output_path.joinpath(
                    self.analysis.name.replace(" ", "_") + "_results.xlsx"
                ),
                index=False,
            )

        return _analysis_result_wrapper
