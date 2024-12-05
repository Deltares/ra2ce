from pathlib import Path

import networkx as nx
import pandas as pd
from geopandas import GeoDataFrame, read_feather
from shapely.geometry import LineString, MultiLineString
from tqdm import tqdm

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.traffic_analysis.traffic_analysis_factory import (
    TrafficAnalysisFactory,
)
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.network_config_data import (
    OriginsDestinationsSection,
)


class OptimalRouteOriginDestination(AnalysisBase, AnalysisLossesProtocol):
    analysis: AnalysisSectionLosses
    graph_file: GraphFile
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames
    origins_destinations: OriginsDestinationsSection

    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
    ) -> None:
        self.analysis = analysis_input.analysis
        self.graph_file = analysis_input.graph_file
        self.input_path = analysis_input.input_path
        self.static_path = analysis_input.static_path
        self.output_path = analysis_input.output_path
        self.hazard_names = analysis_input.hazard_names
        self.origins_destinations = analysis_input.origins_destinations

    @staticmethod
    def extract_od_nodes_from_graph(
        graph: nx.MultiGraph,
    ) -> list[tuple[str, str]]:
        """
        Extracts all Origin - Destination nodes from the graph, prevents from entries
        with list of nodes for a node.

        Args:
            graph (nx.MultiGraph): Graph containing origin-destination nodes.

        Returns:
            list[tuple[str, str]]]: List containing tuples of origin - destination node combinations.
        """
        _od_nodes = []
        for n, v in graph.nodes(data=True):
            if "od_id" not in v:
                continue
            _o_node_list = list(map(lambda x: (n, x), v["od_id"].split(",")))
            _od_nodes.extend(_o_node_list)
        return _od_nodes

    @staticmethod
    def find_route_ods(
        graph: nx.MultiGraph,
        od_nodes: list[tuple[tuple[str, str], tuple[str, str]]],
        weighing: WeighingEnum,
    ) -> GeoDataFrame:
        # create the routes between all OD pairs
        (
            o_node_list,
            d_node_list,
            origin_list,
            destination_list,
            opt_path_list,
            weighing_list,
            match_ids_list,
            geometries_list,
        ) = ([], [], [], [], [], [], [], [])
        for o, d in tqdm(od_nodes, desc="Finding optimal routes."):
            if nx.has_path(graph, o[0], d[0]):
                # calculate the length of the preferred route and preferred route nodes
                [pref_route, pref_nodes] = nx.single_source_dijkstra(
                    graph, o[0], d[0], weight=weighing.config_value
                )

                # found out which edges belong to the preferred path
                edgesinpath = list(zip(pref_nodes[0:], pref_nodes[1:]))

                pref_edges = []
                match_list = []
                for u, v in edgesinpath:
                    # get edge with the lowest weighing if there are multiple edges that connect u and v
                    _uv_graph = graph[u][v]
                    edge_key = sorted(
                        _uv_graph,
                        key=lambda x, _fgraph=_uv_graph: _fgraph[x][
                            weighing.config_value
                        ],
                    )[0]
                    _uv_graph_edge = _uv_graph[edge_key]
                    if "geometry" in _uv_graph_edge:
                        pref_edges.append(_uv_graph_edge["geometry"])
                    else:
                        pref_edges.append(
                            LineString(
                                [graph.nodes[u]["geometry"], graph.nodes[v]["geometry"]]
                            )
                        )
                    if "rfid" in _uv_graph_edge:
                        match_list.append(_uv_graph_edge["rfid"])

                combined_pref_edges = MultiLineString([])
                for geometry in pref_edges:
                    combined_pref_edges = combined_pref_edges.union(geometry)

                if not combined_pref_edges.is_valid:
                    print(combined_pref_edges.is_valid)
                    print(o[0], d[0])

                # save all data to lists (of lists)
                o_node_list.append(o[0])
                d_node_list.append(d[0])
                origin_list.append(o[1])
                destination_list.append(d[1])
                opt_path_list.append(pref_nodes)
                weighing_list.append(pref_route)
                match_ids_list.append(match_list)
                geometries_list.append(combined_pref_edges)
                # geometries_list.append(pref_edges)

        # Geodataframe to save all the optimal routes
        pref_routes = GeoDataFrame(
            {
                "o_node": o_node_list,
                "d_node": d_node_list,
                "origin": origin_list,
                "destination": destination_list,
                "opt_path": opt_path_list,
                weighing.config_value: weighing_list,
                "match_ids": match_ids_list,
                "geometry": geometries_list,
            },
            geometry="geometry",
            crs="epsg:4326",
        )
        # Remove potential duplicates (o, d node) with a different Origin name.
        _duplicate_columns = ["o_node", "d_node", "destination", "length", "geometry"]
        pref_routes = pref_routes.drop_duplicates(
            subset=_duplicate_columns, keep="first"
        ).reset_index(drop=True)
        return pref_routes

    def _get_origin_destination_pairs(
        self, graph: nx.MultiGraph
    ) -> list[tuple[tuple[str, str], tuple[str, str]]]:
        od_path = self.static_path.joinpath(
            "output_graph", "origin_destination_table.feather"
        )
        od = read_feather(od_path)
        od_pairs = [
            (a, b)
            for a in od.loc[od["o_id"].notnull(), "o_id"]
            for b in od.loc[od["d_id"].notnull(), "d_id"]
        ]
        all_nodes = self.extract_od_nodes_from_graph(graph)
        od_nodes = []
        for aa, bb in od_pairs:
            # it is possible that there are multiple origins/destinations at the same 'entry-point' in the road
            od_nodes.append(
                (
                    [
                        (n, n_name)
                        for n, n_name in all_nodes
                        if (n_name == aa) | (aa in n_name)
                    ][0],
                    [
                        (n, n_name)
                        for n, n_name in all_nodes
                        if (n_name == bb) | (bb in n_name)
                    ][0],
                )
            )
        return od_nodes

    def optimal_route_origin_destination(
        self, graph: nx.MultiGraph, analysis: AnalysisSectionLosses
    ) -> GeoDataFrame:
        # create list of origin-destination pairs
        od_nodes = self._get_origin_destination_pairs(graph)
        pref_routes = self.find_route_ods(graph, od_nodes, analysis.weighing)
        return pref_routes

    def optimal_route_od_link(
        self,
        road_network: GeoDataFrame,
        od_table: GeoDataFrame,
        equity: pd.DataFrame,
    ) -> pd.DataFrame:
        return TrafficAnalysisFactory.get_analysis(
            road_network,
            od_table,
            self.origins_destinations.destinations_names,
            equity,
        ).optimal_route_od_link()

    def execute(self) -> AnalysisResultWrapper:
        _output_path = self.output_path.joinpath(self.analysis.analysis.config_value)

        gdf = self.optimal_route_origin_destination(
            self.graph_file.get_graph(), self.analysis
        )

        if self.analysis.save_traffic and hasattr(
            self.origins_destinations, "origin_count"
        ):
            od_table = read_feather(
                self.static_path.joinpath(
                    "output_graph", "origin_destination_table.feather"
                )
            )
            _equity_weights_file = None
            if self.analysis.equity_weight:
                _equity_weights_file = self.static_path.joinpath(
                    "network", self.analysis.equity_weight
                )
            route_traffic_df = self.optimal_route_od_link(
                gdf,
                od_table,
                TrafficAnalysisFactory.read_equity_weights(_equity_weights_file),
            )
            impact_csv_path = _output_path.joinpath(
                (self.analysis.name.replace(" ", "_") + "_link_traffic.csv"),
            )
            route_traffic_df.to_csv(impact_csv_path, index=False)

        return self.generate_result_wrapper(gdf)
