from pathlib import Path

import networkx as nx
import numpy as np
import osmnx
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect,
)
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.network.graph_files.graph_file import GraphFile


class SingleLinkRedundancy(AnalysisIndirectProtocol):
    graph_file: GraphFile
    analysis: AnalysisSectionIndirect
    input_path: Path = None
    output_path: Path = None
    result: GeoDataFrame = None

    def __init__(
        self,
        graph_file: GraphFile,
        analysis: AnalysisSectionIndirect,
        input_path: Path,
        output_path: Path,
    ) -> None:
        self.graph_file = graph_file
        self.analysis = analysis
        self.input_path = input_path
        self.output_path = output_path

    def execute(self) -> GeoDataFrame:
        # TODO adjust to the right names of the RA2CE tool
        # if 'road_usage_data_path' in InputDict:
        #     road_usage_data = pd.read_excel(InputDict.road_usage_data_path)
        #     road_usage_data.dropna(axis=0, how='all', subset=['vehicle_type'], inplace=True)
        #     aadt_names = [aadt_name for aadt_name in road_usage_data['attribute_name'] if aadt_name == aadt_name]
        # else:
        #     aadt_names = None
        #     road_usage_data = pd.DataFrame()

        # create a geodataframe from the graph
        gdf = osmnx.graph_to_gdfs(self.graph_file.graph, nodes=False)

        # list for the length of the alternative routes
        alt_dist_list = []
        alt_nodes_list = []
        dif_dist_list = []
        detour_exist_list = []
        for e_remove in list(self.graph_file.graph.edges.data(keys=True)):
            u, v, k, data = e_remove

            # if data['highway'] in attr_list:
            # remove the edge
            self.graph_file.graph.remove_edge(u, v, k)

            if nx.has_path(self.graph_file.graph, u, v):
                # calculate the alternative distance if that edge is unavailable
                alt_dist = nx.dijkstra_path_length(
                    self.graph_file.graph,
                    u,
                    v,
                    weight=self.analysis.weighing.config_value,
                )
                alt_dist_list.append(alt_dist)

                # append alternative route nodes
                alt_nodes = nx.dijkstra_path(self.graph_file.graph, u, v)
                alt_nodes_list.append(alt_nodes)

                # calculate the difference in distance
                dif_dist_list.append(
                    alt_dist - data[self.analysis.weighing.config_value]
                )

                detour_exist_list.append(1)
            else:
                alt_dist_list.append(np.NaN)
                alt_nodes_list.append(np.NaN)
                dif_dist_list.append(np.NaN)
                detour_exist_list.append(0)

            # add edge again to the graph
            self.graph_file.graph.add_edge(u, v, k, **data)

        # Add the new columns to the geodataframe
        gdf["alt_dist"] = alt_dist_list
        gdf["alt_nodes"] = alt_nodes_list
        gdf["diff_dist"] = dif_dist_list
        gdf["detour"] = detour_exist_list

        # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
        # todo: input here this option

        return gdf
