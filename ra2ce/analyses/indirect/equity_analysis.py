"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import itertools
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import geopandas as gpd
import ast


class EquityAnalysis:
    gdf: gpd.GeoDataFrame
    od_table: gpd.GeoDataFrame
    destinations_names: list[str]

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        od_table: gpd.GeoDataFrame,
        destination_names: list[str],
    ) -> None:
        """
        Args:
            gdf (gpd.GeoDataFrame): Geodataframe containing the overall network information.
            od_table (gpd.GeoDataFrame): GeoDataFrame representing the Origins - Destinations table.
            destination_names (list[str]): List of destinations nodes.
        """
        self.gdf = gdf
        self.od_table = od_table
        self.destinations_names = destination_names

    @staticmethod
    def read_equity_weights(equity_weight_file: Path) -> pd.DataFrame:
        """
        Reads the equity data from a geojson fileand loads it into a pandas dataframe.

        Args:
            equity_weight_file (Path): File containing values of region and weight.

        Returns:
            pd.DataFrame: Dataframe representing the geojson data.
        """
        if not equity_weight_file or not equity_weight_file.exists():
            return pd.DataFrame()

        _separator = (
            ";" if ";" in equity_weight_file.read_text().splitlines()[0] else ","
        )
        return pd.read_csv(equity_weight_file, sep=_separator)

    @staticmethod
    def get_opt_path_values(opt_path: Any) -> list[Any]:
        if isinstance(opt_path, list):
            return opt_path
        return ast.literal_eval(opt_path)

    def _get_values_prioritarian(
        self, equity_data: pd.DataFrame, od_table_data: gpd.GeoDataFrame
    ) -> np.array:
        prioritarian_mapping = dict(zip(equity_data["region"], equity_data["weight"]))
        prioritarian_mapping.update({"Not assigned": 1})
        return (
            od_table_data["region"].map(prioritarian_mapping) * od_table_data["values"]
        )

    def analyze_with_weights(
        self,
        equity_data_file: Path,
    ) -> pd.DataFrame:
        """
        Generates a pandas `DataFrame` with the optimal traffic routes including results for `equal` and `prioritarian`.

        Args:
            equity_data_file (Path): File containing the region's equity relations.

        Returns:
            pd.DataFrame: Resulting dataframe with optimal origin-destination routes.
        """
        _equity_weights_data = self.read_equity_weights(equity_data_file)
        return self.optimal_route_od_link(_equity_weights_data)

    def _get_calculated_traffic(
        self, origin_node: str, value_key: str, count_destination_nodes: int
    ) -> gpd.GeoDataFrame:
        return (
            self.od_table.loc[
                self.od_table["o_id"] == origin_node,
                value_key,
            ].values[0]
            / count_destination_nodes
        )

    def _get_traffic_in_origin_node(
        self,
        node_idx: int,
        origin_node: str,
        current_traffic: float,
        value_key: str,
        count_destination_nodes: int,
    ) -> float:
        _calculated_traffic = self._get_calculated_traffic(
            origin_node, value_key, count_destination_nodes
        )
        if node_idx == 0:
            return current_traffic * _calculated_traffic
        return current_traffic + _calculated_traffic

    def _get_origin_nodes_traffic(
        self,
        o_nodes: list[str],
        regular_traffic: float,
        equalitary_traffic: float,
        prioritarian_taffic: float,
        count_destination_nodes: int,
        with_equity_data: bool,
    ) -> tuple[float, float, float]:
        o_num = len(o_nodes)
        j_ = 0
        for o_n in o_nodes:
            if self.destinations_names in o_n:
                j_ -= 1
                o_num -= 1
                continue
            regular_traffic = self._get_traffic_in_origin_node(
                j_, o_n, regular_traffic, "values", count_destination_nodes
            )
            if with_equity_data:
                prioritarian_taffic = self._get_traffic_in_origin_node(
                    j_,
                    o_n,
                    prioritarian_taffic,
                    "values_prioritarian",
                    count_destination_nodes,
                )
            j_ += 1

        equalitary_traffic *= o_num
        return regular_traffic, equalitary_traffic, prioritarian_taffic

    def optimal_route_od_link(
        self,
        equity_data: pd.DataFrame,
    ) -> pd.DataFrame:
        origin_nodes = np.unique(self.gdf["origin"])
        destination_nodes = np.unique(self.gdf["destination"])

        unique_destination_nodes = np.unique(list(self.od_table["d_id"].fillna("0")))
        count_destination_nodes = len([x for x in unique_destination_nodes if x != "0"])

        route_traffic = {}
        route_traffic_equal = {}
        route_traffic_prioritarian = {}

        if any(equity_data):
            self.od_table["values_prioritarian"] = self._get_values_prioritarian(
                equity_data, self.od_table
            )

        def _set_traffic_routes(
            nodes_key: str,
            total_traffic: float,
            total_equalitary_traffic: float,
            total_prioritarian_traffic: float,
        ) -> None:
            route_traffic[nodes_key] = total_traffic + route_traffic.get(nodes_key, 0)
            route_traffic_equal[
                nodes_key
            ] = total_equalitary_traffic + route_traffic_equal.get(nodes_key, 0)
            if any(equity_data):
                route_traffic_prioritarian[
                    nodes_key
                ] = total_prioritarian_traffic + route_traffic_prioritarian.get(
                    nodes_key, 0
                )

        nodes_list = []
        for o_node in origin_nodes:
            for d_node in destination_nodes:
                opt_path = self.get_opt_path_values(
                    self.gdf.loc[
                        (self.gdf["origin"] == o_node)
                        & (self.gdf["destination"] == d_node),
                        "opt_path",
                    ].values[0]
                )
                for u_node, v_node in itertools.pairwise(opt_path):
                    nodes_list.append((u_node, v_node))
                    _nodes_key_name = f"{u_node}_{v_node}"
                    _total_traffic = 1
                    t_eq = 1
                    if any(equity_data):
                        t_prioritarian = 1
                    if "," in o_node:
                        (
                            _total_traffic,
                            t_eq,
                            t_prioritarian,
                        ) = self._get_origin_nodes_traffic(
                            o_node.split(","),
                            _total_traffic,
                            t_eq,
                            t_prioritarian,
                            count_destination_nodes,
                            any(equity_data),
                        )
                    else:
                        _total_traffic *= self._get_calculated_traffic(
                            o_node, "values", count_destination_nodes
                        )
                        if any(equity_data):
                            t_prioritarian *= self._get_calculated_traffic(
                                o_node, "values_prioritarian", count_destination_nodes
                            )
                    if "," in d_node:
                        d_num = len(d_node.split(","))
                        t_eq *= d_num
                        _total_traffic *= d_num
                        if any(equity_data):
                            t_prioritarian *= d_num

                    _set_traffic_routes(
                        _nodes_key_name, _total_traffic, t_eq, t_prioritarian
                    )

        u_list, v_list = zip(*nodes_list)
        t_list = route_traffic.values()
        teq_list = route_traffic_equal.values()
        if any(equity_data):
            tprioritarian_list = route_traffic_prioritarian.values()
            data_tuples = list(
                zip(u_list, v_list, t_list, teq_list, tprioritarian_list)
            )
            route_traffic_df = pd.DataFrame(
                data_tuples,
                columns=[
                    "u",
                    "v",
                    "traffic",
                    "traffic_egalitarian",
                    "traffic_prioritarian",
                ],
            )
        else:
            data_tuples = list(zip(u_list, v_list, t_list, teq_list))
            route_traffic_df = pd.DataFrame(
                data_tuples, columns=["u", "v", "traffic", "traffic_egalitarian"]
            )

        return route_traffic_df
