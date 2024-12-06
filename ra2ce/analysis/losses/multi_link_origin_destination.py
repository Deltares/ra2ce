import copy
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame, read_feather, read_file

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.optimal_route_origin_destination import (
    OptimalRouteOriginDestination,
)
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.network_config_data import (
    OriginsDestinationsSection,
)


class MultiLinkOriginDestination(AnalysisBase, AnalysisLossesProtocol):
    analysis: AnalysisSectionLosses
    graph_file_hazard: GraphFile
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames
    origins_destinations: OriginsDestinationsSection
    _analysis_input: AnalysisInputWrapper

    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
    ) -> None:
        self.analysis = analysis_input.analysis
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.static_path = analysis_input.static_path
        self.output_path = analysis_input.output_path
        self.hazard_names = analysis_input.hazard_names
        self.origins_destinations = analysis_input.origins_destinations
        self._analysis_input = analysis_input

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

    def _get_origin_destination_pairs(
        self, graph: nx.MultiGraph
    ) -> list[tuple[str, str], tuple[str, str]]:
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

    def multi_link_origin_destination(
        self, graph: nx.MultiGraph, analysis: AnalysisSectionLosses
    ) -> GeoDataFrame:
        """Calculates the connectivity between origins and destinations"""
        od_nodes = self._get_origin_destination_pairs(graph)

        all_results = []
        for hazard in self.hazard_names.names:
            hazard_name = self.hazard_names.get_name(hazard)

            graph_hz = copy.deepcopy(graph)

            # Check if the o/d pairs are still connected while some links are disrupted by the hazard(s)
            edges_remove = [
                e for e in graph.edges.data(keys=True) if hazard_name in e[-1]
            ]
            edges_remove = [e for e in edges_remove if (e[-1][hazard_name] is not None)]
            edges_remove = [
                e
                for e in edges_remove
                if (e[-1][hazard_name] > float(analysis.threshold))
                & ("bridge" not in e[-1])
            ]
            graph_hz.remove_edges_from(edges_remove)

            # convert the networkx graph to igraph object to speed up the route finding algorithm
            # igraph_hz = ig.Graph.from_networkx(igraph_hz)

            # Find the routes
            od_routes = OptimalRouteOriginDestination.find_route_ods(
                graph_hz, od_nodes, analysis.weighing
            )
            od_routes["hazard"] = hazard_name
            all_results.append(od_routes)

        return pd.concat(all_results, ignore_index=True)

    def multi_link_origin_destination_impact(
        self, gdf: GeoDataFrame, gdf_ori: GeoDataFrame
    ) -> tuple[pd.DataFrame, GeoDataFrame]:
        """Calculates some default indicators that quantify the impacts of disruptions to origin-destination flows
        The function outputs the following file:

        1. gdf_ori (multi_link_origin_destination_impact.csv), containing the following information:
            - origin and destination node
            - length: initial shortest path length before disruptions
            - length_hazardName: shortest path length after disruption
            - diff_length_hazardName: increase in shortest path length after disruption (length_hazardName - length)
            - diff_length_hazardName_pc: same as above, but as a fraction of initial length

        2. diff_df (multi_link_origin_destination_impact_summary.csv), containing the following information:
            - hazard: hazard name
            - od_disconnected_abs: number of OD disconnected
            - od_disconnected_pc (%): percentage of OD disconnected
            - origin_disconnected_abs: number of origin points disconnected
            - origin_disconnected_pc (%): percentage of origin points disconnected
            - destination_disconnected_abs: number of destination points disconnected
            - destination_disconnected_pc (%): percentage of destination points disconnected
            - max_increase_abs: maximum increase in travel length across all OD pairs
            - mean_increase_abs: mean increase in travel length across all OD pairs
            - median_increase_abs: median increase in travel length across all OD pairs
            - max_increase_pc, mean_increase_pc, median_increase_pc (%): same as above three, but as a percentage relative to no-hazard
        """

        hazard_list = np.unique(gdf["hazard"])

        # calculate number of disconnected origin, destination, and origin-destination pair
        # TODO: there seems to be an issue in calculating origin_count and destination_count where origin and destination nodes are the same, e.g., A_25,B_1
        gdf["OD"] = gdf["origin"] + gdf["destination"]
        gdf_ori["OD"] = gdf_ori["origin"] + gdf_ori["destination"]
        # origin
        gdf_ori["origin_count"] = gdf_ori["origin"].apply(lambda x: len(x.split(",")))
        init_origins = gdf_ori.groupby("origin")["origin_count"].sum()
        del gdf_ori["origin_count"]
        # destination
        gdf_ori["destination_count"] = gdf_ori["destination"].apply(
            lambda x: len(x.split(","))
        )
        init_destinations = gdf_ori.groupby("destination")["destination_count"].sum()
        del gdf_ori["destination_count"]
        # od pairs
        init_od_pairs = init_origins * init_destinations
        abs_od_disconnected = []
        share_od_disconnected = []
        abs_origin_disconnected = []
        share_origin_disconnected = []
        abs_destination_disconnected = []
        share_destination_disconnected = []
        for hz in hazard_list:
            gdf_ = gdf.loc[gdf["hazard"] == hz]

            gdf_["origin_count"] = gdf_["origin"].apply(lambda x: len(x.split(",")))
            remaining_origins = gdf_.groupby("origin")["origin_count"].sum()
            del gdf_["origin_count"]
            diff_origins = init_origins - remaining_origins
            abs_origin_disconnected.append(diff_origins)
            share_origin_disconnected.append(100 * diff_origins / init_origins)

            gdf_["destination_count"] = gdf_["destination"].apply(
                lambda x: len(x.split(","))
            )
            remaining_destinations = gdf_.groupby("destination")[
                "destination_count"
            ].sum()
            del gdf_["destination_count"]
            diff_destinations = init_destinations - remaining_destinations
            abs_destination_disconnected.append(diff_destinations)
            share_destination_disconnected.append(
                100 * diff_destinations / init_destinations
            )

            remaining_od_pairs = remaining_origins * remaining_destinations
            diff_od_pairs = init_od_pairs - remaining_od_pairs
            abs_od_disconnected.append(diff_od_pairs)
            share_od_disconnected.append(100 * diff_od_pairs / init_od_pairs)

        # calculate change in travel time/distance
        max_increase_abs = []
        min_increase_abs = []
        mean_increase_abs = []
        median_increase_abs = []
        max_increase_pc = []
        min_increase_pc = []
        mean_increase_pc = []
        median_increase_pc = []
        for hz in hazard_list:
            gdf_ = gdf.loc[gdf["hazard"] == hz][["OD", "length"]]
            gdf_.columns = ["OD", "length_" + hz]
            gdf_ori = gdf_ori.merge(gdf_, how="left", on="OD")
            gdf_ori.drop_duplicates(subset="OD", inplace=True)
            gdf_ori["diff_length_" + hz] = gdf_ori["length_" + hz] - gdf_ori["length"]
            gdf_ori["diff_length_" + hz + "_pc"] = (
                100 * gdf_ori["diff_length_" + hz] / gdf_ori["length"]
            )

            max_increase_abs.append(np.nanmax(gdf_ori["diff_length_" + hz]))
            min_increase_abs.append(np.nanmin(gdf_ori["diff_length_" + hz]))
            mean_increase_abs.append(np.nanmean(gdf_ori["diff_length_" + hz]))
            median_increase_abs.append(np.nanmedian(gdf_ori["diff_length_" + hz]))

            max_increase_pc.append(np.nanmax(gdf_ori["diff_length_" + hz + "_pc"]))
            min_increase_pc.append(np.nanmin(gdf_ori["diff_length_" + hz + "_pc"]))
            mean_increase_pc.append(np.nanmean(gdf_ori["diff_length_" + hz + "_pc"]))
            median_increase_pc.append(
                np.nanmedian(gdf_ori["diff_length_" + hz + "_pc"])
            )

        diff_df = pd.DataFrame()
        diff_df["hazard"] = hazard_list

        diff_df["od_disconnected_abs"] = abs_od_disconnected
        diff_df["od_disconnected_pc (%)"] = share_od_disconnected
        diff_df["origin_disconnected_abs"] = abs_origin_disconnected
        diff_df["origin_disconnected_pc (%)"] = share_origin_disconnected
        diff_df["destination_disconnected_abs"] = abs_destination_disconnected
        diff_df["destination_disconnected_pc (%)"] = share_destination_disconnected

        diff_df["max_increase_abs"] = max_increase_abs
        diff_df["min_increase_abs"] = min_increase_abs
        diff_df["mean_increase_abs"] = mean_increase_abs
        diff_df["median_increase_abs"] = median_increase_abs
        diff_df["max_increase_pc (%)"] = max_increase_pc
        diff_df["min_increase_pc (%)"] = min_increase_pc
        diff_df["mean_increase_pc (%)"] = mean_increase_pc
        diff_df["median_increase_pc (%)"] = median_increase_pc

        return diff_df, gdf_ori

    def multi_link_origin_destination_regional_impact(
        self, gdf_ori: GeoDataFrame
    ) -> tuple[GeoDataFrame, GeoDataFrame]:
        """
        Aggregation of the impacts of disruptions at region level
        Users need to specify 'region' and 'region_var' attributes in the network.ini file
        See the Pontianak case study for an example

        The function outputs the following files:
        1. multi_link_origin_destination_regional_impact.csv
            Impacts of disruption aggregated for each origin node. Region information (to which region an origin node belongs) is retained

        2. multi_link_origin_destination_regional_impact_summary.csv
            Impacts of disruption aggregated for each region.

        In both files, the following information is stored:
            - init_length: initial average length to all destination nodes (for each origin node and for each region)
            - init_destination: initial number of destination nodes
            - hazardName_pc_increase: average increase in travel time to all destination nodes (percentage relative to initial travel time, for each origin node and for each region)
            - hazardName_pc_disconnect: average number of OD pairs disconnected (relative to initial number of OD pairs, for each origin node and for each region)
        """

        gdf_ori_ = gdf_ori.copy()

        # read origin points
        origin_fn = Path(self.static_path).joinpath(
            "output_graph", "origin_destination_table.gpkg"
        )
        origin = read_file(origin_fn, engine="pyogrio")
        index = [isinstance(x, str) for x in origin["o_id"]]
        origin = origin[index]
        origin.reset_index(inplace=True, drop=True)

        # record where each origin point resides
        origin_mapping = {}
        for o in np.unique(origin["o_id"]):
            r = origin.loc[origin["o_id"] == o, "region"].values[0]
            origin_mapping.update({o: r})

        # record impact to each region
        origin_impact_master = pd.DataFrame()
        for r in np.unique(origin["region"]):
            origin_points = list(origin.loc[origin["region"] == r, "o_id"].values)
            for o in origin_points:
                origin_impact_tosave = pd.DataFrame()
                origin_impact_tosave.loc[0, "o_id"] = o
                origin_impact_tosave.loc[0, "region"] = r

                origin_impact = gdf_ori_.loc[gdf_ori_["origin"].str.contains(o)]

                # initial condition
                origin_impact_tosave.loc[0, "init_length"] = np.mean(
                    origin_impact["length"]
                )
                origin_impact_tosave.loc[0, "init_destination"] = len(
                    np.unique(origin_impact["destination"])
                )

                # impact of each hazard
                for col in origin_impact.columns:
                    if "_pc" in col:
                        delta = np.nanmean(origin_impact[col])
                        if delta < 0:
                            delta = 0
                        origin_impact_tosave.loc[0, col[12:] + "_increase"] = delta

                        disconnected = origin_impact[col].isna().sum()
                        origin_impact_tosave.loc[0, col[12:] + "_disconnect"] = (
                            100
                            * disconnected
                            / origin_impact_tosave["init_destination"].values[0]
                        )

                origin_impact_master = origin_impact_master.append(origin_impact_tosave)

        region_impact_master = origin_impact_master[origin_impact_master.columns[1:]]
        region_impact_master = region_impact_master.groupby(by="region").mean()

        return origin_impact_master, region_impact_master

    def execute(self) -> AnalysisResultWrapper:
        _output_path = self.output_path.joinpath(self.analysis.analysis.config_value)
        gdf = self.multi_link_origin_destination(
            self.graph_file_hazard.get_graph(), self.analysis
        )
        self._analysis_input.graph_file = self._analysis_input.graph_file_hazard
        _orod_result_wrapper = OptimalRouteOriginDestination(
            self._analysis_input
        ).execute()
        (disruption_impact_df, gdf_ori,) = self.multi_link_origin_destination_impact(
            gdf, _orod_result_wrapper.get_single_result()
        )
        try:
            assert self.origins_destinations.region
            (
                regional_impact_df,
                regional_impact_summary_df,
            ) = self.multi_link_origin_destination_regional_impact(gdf_ori)
            impact_csv_path = _output_path.joinpath(
                (self.analysis.name.replace(" ", "_") + "_regional_impact.csv"),
            )
            regional_impact_df.to_csv(impact_csv_path, index=False)
            impact_csv_path = _output_path.joinpath(
                (self.analysis.name.replace(" ", "_") + "_regional_impact_summary.csv"),
            )
            regional_impact_summary_df.to_csv(impact_csv_path)
        except Exception:
            pass
        impact_csv_path = _output_path.joinpath(
            (self.analysis.name.replace(" ", "_") + "_impact.csv"),
        )
        del gdf_ori["geometry"]
        gdf_ori.to_csv(impact_csv_path, index=False)
        impact_csv_path = _output_path.joinpath(
            (self.analysis.name.replace(" ", "_") + "_impact_summary.csv"),
        )
        disruption_impact_df.to_csv(impact_csv_path, index=False)

        return self.generate_result_wrapper(gdf)
