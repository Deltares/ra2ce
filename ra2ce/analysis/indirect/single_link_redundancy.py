from pathlib import Path

import networkx as nx
import numpy as np
import osmnx
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.analysis.indirect.weighing_analysis.weighing_analysis_factory import (
    WeighingAnalysisFactory,
)
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames


class SingleLinkRedundancy(AnalysisIndirectProtocol):
    analysis: AnalysisSectionIndirect
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
        _alt_value_list = []
        _alt_nodes_list = []
        _diff_value_list = []
        _detour_exist_list = []

        _weighing_analyser = WeighingAnalysisFactory.get_analysis(
            self.analysis.weighing
        )
        for e_remove in list(self.graph_file.graph.edges.data(keys=True)):
            u, v, k, _weighing_analyser.weighing_data = e_remove

            # if data['highway'] in attr_list:
            # remove the edge
            self.graph_file.graph.remove_edge(u, v, k)

            if nx.has_path(self.graph_file.graph, u, v):
                # calculate the alternative distance if that edge is unavailable
                alt_dist = nx.dijkstra_path_length(
                    self.graph_file.graph, u, v, weight=WeighingEnum.LENGTH.config_value
                )
                alt_nodes = nx.dijkstra_path(self.graph_file.graph, u, v)
                alt_value = _weighing_analyser.calculate_alternative_distance(alt_dist)

                # append alternative route nodes
                _alt_value_list.append(alt_value)
                _alt_nodes_list.append(alt_nodes)

                # calculate the difference in distance
                _diff_value_list.append(
                    round(
                        alt_value
                        - _weighing_analyser.weighing_data[
                            self.analysis.weighing.config_value
                        ],
                        2,
                    )
                )

                _detour_exist_list.append(1)
            else:
                _alt_value_list.append(_weighing_analyser.calculate_distance())
                _alt_nodes_list.append(np.NaN)
                _diff_value_list.append(np.NaN)
                _detour_exist_list.append(0)

            # add edge again to the graph
            self.graph_file.graph.add_edge(u, v, k, **_weighing_analyser.weighing_data)

        # Add the new columns to the geodataframe
        _weighing_analyser.extend_graph(_gdf_graph)
        _gdf_graph[f"alt_{self.analysis.weighing.config_value}"] = _alt_value_list
        _gdf_graph["alt_nodes"] = _alt_nodes_list
        _gdf_graph[f"diff_{self.analysis.weighing.config_value}"] = _diff_value_list
        _gdf_graph["detour"] = _detour_exist_list

        # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
        # todo: input here this option

        return _gdf_graph
