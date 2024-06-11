import math
from pathlib import Path

import networkx as nx
import osmnx
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_factory import (
    WeighingAnalysisFactory,
)
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames


class SingleLinkRedundancy(AnalysisLossesProtocol):
    analysis: AnalysisSectionLosses
    graph_file: GraphFile
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames

    def __init__(self, analysis_input: AnalysisInputWrapper) -> None:
        self.analysis = analysis_input.analysis
        self.graph_file = analysis_input.graph_file
        self.input_path = analysis_input.input_path
        self.static_path = analysis_input.static_path
        self.output_path = analysis_input.output_path
        self.hazard_names = analysis_input.hazard_names
        self.result = None

    def execute(self) -> GeoDataFrame:
        """This is the function to analyse roads with a single link disruption and an alternative route."""
        # TODO adjust to the right names of the RA2CE tool
        # if 'road_usage_data_path' in InputDict:
        #     road_usage_data = pd.read_excel(InputDict.road_usage_data_path)
        #     road_usage_data.dropna(axis=0, how='all', subset=['vehicle_type'], inplace=True)
        #     aadt_names = [aadt_name for aadt_name in road_usage_data['attribute_name'] if aadt_name == aadt_name]
        # else:
        #     aadt_names = None
        #     road_usage_data = pd.DataFrame()

        # create a geodataframe from the graph
        _gdf_graph = osmnx.graph_to_gdfs(self.graph_file.get_graph(), nodes=False)

        # list for the length of the alternative routes
        _current_value_list = []
        _alt_value_list = []
        _alt_nodes_list = []
        _diff_value_list = []
        _detour_exist_list = []

        _weighing_analyser = WeighingAnalysisFactory.get_analysis(
            self.analysis.weighing, _gdf_graph
        )

        # Ensure each edge has a valid weighing attribute
        for edge in list(self.graph_file.graph.edges.data(keys=True)):
            u, v, k, _weighing_analyser.edge_data = edge
            _current_value_list.append(_weighing_analyser.get_current_value())

        # Loop over all edges to temporarily remove them and calculate the alternative route
        for e, e_remove in enumerate(list(self.graph_file.graph.edges.data(keys=True))):
            u, v, k, _weighing_analyser.edge_data = e_remove

            # remove the edge
            self.graph_file.graph.remove_edge(u, v, k)

            if nx.has_path(self.graph_file.graph, u, v):

                # calculate the alternative distance if that edge is unavailable
                _alt_dist = nx.dijkstra_path_length(
                    self.graph_file.graph,
                    u,
                    v,
                    weight=self.analysis.weighing.config_value,
                )
                _alt_nodes = nx.dijkstra_path(self.graph_file.graph, u, v)
                _alt_value = _weighing_analyser.calculate_alternative_value(_alt_dist)

                # append alternative route nodes
                _alt_value_list.append(_alt_value)
                _alt_nodes_list.append(_alt_nodes)

                # calculate the difference in distance
                _diff_value_list.append(round(_alt_value - _current_value_list[e], 3))

                _detour_exist_list.append(1)
            else:
                _alt_value_list.append(_current_value_list[e])
                _alt_nodes_list.append(math.nan)
                _diff_value_list.append(math.nan)
                _detour_exist_list.append(0)

            # add edge again to the graph
            self.graph_file.graph.add_edge(u, v, k, **_weighing_analyser.edge_data)

        # Add the new columns to the geodataframe
        _gdf_graph[self.analysis.weighing.config_value] = _current_value_list
        _gdf_graph[f"alt_{self.analysis.weighing.config_value}"] = _alt_value_list
        _gdf_graph["alt_nodes"] = _alt_nodes_list
        _gdf_graph[f"diff_{self.analysis.weighing.config_value}"] = _diff_value_list
        _gdf_graph["detour"] = _detour_exist_list

        # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
        # todo: input here this option

        return _gdf_graph
