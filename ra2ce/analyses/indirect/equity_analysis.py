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
        gdf: gpd.GeoDataFrame,
        od_table: gpd.GeoDataFrame,
        equity_data_file: Path,
        destination_names: list[str],
    ) -> pd.DataFrame:
        """
        Generates a pandas `DataFrame` with the optimal traffic routes including results for `equal` and `prioritarian`.

        Args:
            gdf (gpd.GeoDataFrame): Geodataframe containing the overall network information.
            od_table (gpd.GeoDataFrame): GeoDataFrame representing the Origins - Destinations table.
            equity_data_file (Path): File containing the region's equity relations.
            destination_names (list[str]): List of destinations nodes.

        Returns:
            pd.DataFrame: Resulting dataframe with optimal origin-destination routes.
        """
        _equity_weights_data = self.read_equity_weights(equity_data_file)
        return self.optimal_route_od_link(
            gdf, od_table, _equity_weights_data, destination_names
        )

    def optimal_route_od_link(
        self,
        gdf: gpd.GeoDataFrame,
        od_table: gpd.GeoDataFrame,
        equity_data: pd.DataFrame,
        destinations_names: list[str],
    ) -> pd.DataFrame:
        origin_nodes = np.unique(gdf["origin"])
        destination_nodes = np.unique(gdf["destination"])

        unique_destination_nodes = np.unique(list(od_table["d_id"].fillna("0")))
        count_destination_nodes = len([x for x in unique_destination_nodes if x != "0"])

        route_traffic = {}
        route_traffic_equal = {}
        route_traffic_prioritarian = {}
        if len(equity_data) > 0:
            route_traffic_prioritarian = {}
            od_table["values_prioritarian"] = self._get_values_prioritarian(
                equity_data, od_table
            )

        def _get_opt_path_values(opt_path: Any) -> list[Any]:
            if isinstance(opt_path, list):
                return opt_path
            return ast.literal_eval(opt_path)

        def _get_calculated_traffic(
            origin_node: str,
            value_key: str,
        ) -> gpd.GeoDataFrame:
            return (
                od_table.loc[
                    od_table["o_id"] == origin_node,
                    value_key,
                ].values[0]
                / count_destination_nodes
            )

        def _get_traffic_in_origin_node(
            node_idx: int, origin_node: str, current_traffic: float, value_key: str
        ) -> float:
            _calculated_traffic = _get_calculated_traffic(origin_node, value_key)
            if node_idx == 0:
                return current_traffic * _calculated_traffic
            return current_traffic + _calculated_traffic

        nodes_list = []
        for o_node in origin_nodes:
            for d_node in destination_nodes:
                opt_path = _get_opt_path_values(
                    gdf.loc[
                        (gdf["origin"] == o_node) & (gdf["destination"] == d_node),
                        "opt_path",
                    ].values[0]
                )
                for u_node, v_node in itertools.pairwise(opt_path):
                    nodes_list.append((u_node, v_node))
                    _nodes_key_name = f"{u_node}_{v_node}"
                    _total_traffic = 1
                    t_eq = 1
                    if len(equity_data) > 0:
                        t_prioritarian = 1
                    if "," in o_node:
                        o_nodes = o_node.split(",")
                        o_num = len(o_nodes)
                        j_ = 0
                        for o_n in o_nodes:
                            if destinations_names in o_n:
                                j_ -= 1
                                o_num -= 1
                                continue

                            _total_traffic = _get_traffic_in_origin_node(
                                j_, o_n, _total_traffic, "values"
                            )
                            if any(equity_data):
                                t_prioritarian = _get_traffic_in_origin_node(
                                    j_, o_n, t_prioritarian, "values_prioritarian"
                                )
                            j_ += 1
                        t_eq *= o_num
                    else:
                        _total_traffic *= _get_calculated_traffic(o_node, "values")
                        if any(equity_data):
                            t_prioritarian *= _get_calculated_traffic(
                                o_node,
                                "values_prioritarian",
                            )
                    if "," in d_node:
                        d_nodes = d_node.split(",")
                        d_num = len(d_nodes)
                        t_eq *= d_num
                        _total_traffic *= d_num
                        if len(equity_data) > 0:
                            t_prioritarian *= d_num

                    try:
                        route_traffic[_nodes_key_name] += _total_traffic
                        route_traffic_equal[_nodes_key_name] += t_eq
                        if len(equity_data) > 0:
                            route_traffic_prioritarian[
                                _nodes_key_name
                            ] += t_prioritarian
                    except Exception:
                        route_traffic.update({_nodes_key_name: _total_traffic})
                        route_traffic_equal.update({_nodes_key_name: t_eq})
                        if len(equity_data) > 0:
                            route_traffic_prioritarian.update(
                                {_nodes_key_name: t_prioritarian}
                            )

        u_list, v_list = zip(*nodes_list)
        t_list = route_traffic.values()
        teq_list = route_traffic_equal.values()
        if len(equity_data) > 0:
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
