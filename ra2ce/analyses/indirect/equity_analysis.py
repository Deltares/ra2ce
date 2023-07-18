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
from typing import Any, Callable
import numpy as np
import pandas as pd
import geopandas as gpd
import ast


class EquityTrafficData:
    regular: dict
    equitarian: dict
    prioritarian: dict
    with_equity: bool

    def __init__(self) -> None:
        self.regular = {}
        self.equitarian = {}
        self.prioritarian = {}
        self.with_equity = False
        self._visited_nodes = []

    @staticmethod
    def get_node_key(left_node: str, right_node: str) -> str:
        return f"{left_node}_{right_node}"

    def add_visited_nodes(self, left_node: str, right_node: str) -> str:
        _node_key = self.get_node_key(left_node, right_node)
        self._visited_nodes.append((left_node, right_node))
        return _node_key

    def update_traffic_routes(
        self,
        nodes_key: str,
        regular_traffic: float,
        equalitary_traffic: float,
        prioritarian_traffic: float,
    ) -> None:
        self.regular[nodes_key] = regular_traffic + self.regular.get(nodes_key, 0)
        self.equitarian[nodes_key] = equalitary_traffic + self.equitarian.get(
            nodes_key, 0
        )
        if self.with_equity:
            self.prioritarian[nodes_key] = prioritarian_traffic + self.prioritarian.get(
                nodes_key, 0
            )

    def get_route_traffic(self, nodes: list[tuple[str, str]]) -> pd.DataFrame:
        u_list, v_list = zip(*self._visited_nodes)
        t_list = self.regular.values()
        teq_list = self.equitarian.values()

        if not self.with_equity:
            data_tuples = list(zip(u_list, v_list, t_list, teq_list))
            return pd.DataFrame(
                data_tuples, columns=["u", "v", "traffic", "traffic_egalitarian"]
            )

        data_tuples = list(
            zip(u_list, v_list, t_list, teq_list, self.prioritarian.values())
        )
        return pd.DataFrame(
            data_tuples,
            columns=[
                "u",
                "v",
                "traffic",
                "traffic_egalitarian",
                "traffic_prioritarian",
            ],
        )


class EquityAnalysis:
    gdf: gpd.GeoDataFrame
    od_table: gpd.GeoDataFrame
    destinations_names: str

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        od_table: gpd.GeoDataFrame,
        destination_names: str,
    ) -> None:
        """
        Args:
            gdf (gpd.GeoDataFrame): Geodataframe containing the overall network information.
            od_table (gpd.GeoDataFrame): GeoDataFrame representing the Origins - Destinations table.
            destination_names (str): Destination nodes.
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

    def _get_node_traffic(
        self, origin_node: str, value_key: str, count_destination_nodes: int
    ) -> gpd.GeoDataFrame:
        return (
            self.od_table.loc[
                self.od_table["o_id"] == origin_node,
                value_key,
            ].values[0]
            / count_destination_nodes
        )

    def _get_origin_nodes_traffic(
        self,
        nodes_list: list[str],
        regular_traffic: float,
        equalitary_traffic: float,
        prioritarian_taffic: float,
        count_destination_nodes: int,
        with_equity_data: bool,
    ) -> tuple[float, float, float]:
        def recalculate_traffic(
            node_idx: int, node: str, value_key: str, traffic_value: float
        ) -> float:
            value = self._get_node_traffic(node, value_key, count_destination_nodes)
            if node_idx == 0:
                return traffic_value * value
            return traffic_value + value

        _calculated_equalitarian = len(
            list(filter(lambda x: self.destinations_names not in x, nodes_list))
        )
        equalitary_traffic *= _calculated_equalitarian

        _intermediate_nodes = 0
        for _node in nodes_list:
            if self.destinations_names in _node:
                _intermediate_nodes -= 1
                continue

            regular_traffic = recalculate_traffic(
                _intermediate_nodes, _node, "values", regular_traffic
            )
            if with_equity_data:
                prioritarian_taffic = recalculate_traffic(
                    _intermediate_nodes,
                    _node,
                    "values_prioritarian",
                    prioritarian_taffic,
                )
            _intermediate_nodes += 1

        return regular_traffic, equalitary_traffic, prioritarian_taffic

    def _get_origin_node_traffic(
        self,
        o_node: str,
        regular_traffic: float,
        equity_traffic: float,
        priority_traffic: float,
        total_d_nodes: int,
        with_equity: bool,
    ) -> tuple[float, float, float]:
        if "," in o_node:
            (
                regular_traffic,
                equity_traffic,
                priority_traffic,
            ) = self._get_origin_nodes_traffic(
                o_node.split(","),
                regular_traffic,
                equity_traffic,
                priority_traffic,
                total_d_nodes,
                with_equity,
            )
        else:
            regular_traffic *= self._get_node_traffic(o_node, "values", total_d_nodes)
            if with_equity:
                priority_traffic *= self._get_node_traffic(
                    o_node, "values_prioritarian", total_d_nodes
                )
        return regular_traffic, equity_traffic, priority_traffic

    def optimal_route_od_link(
        self,
        equity_data: pd.DataFrame,
    ) -> pd.DataFrame:
        origin_nodes = np.unique(self.gdf["origin"])
        destination_nodes = np.unique(self.gdf["destination"])

        unique_destination_nodes = np.unique(list(self.od_table["d_id"].fillna("0")))
        count_destination_nodes = len([x for x in unique_destination_nodes if x != "0"])

        _equity_traffic_data = EquityTrafficData()
        _equity_traffic_data.with_equity = any(equity_data)
        if _equity_traffic_data.with_equity:
            self.od_table["values_prioritarian"] = self._get_values_prioritarian(
                equity_data, self.od_table
            )

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
                    _nodes_key_name = _equity_traffic_data.add_visited_nodes(
                        u_node, v_node
                    )
                    _regular_traffic = 1
                    _equity_traffic = 1
                    if any(equity_data):
                        _priority_traffic = 1
                    if "," in o_node:
                        (
                            _regular_traffic,
                            _equity_traffic,
                            _priority_traffic,
                        ) = self._get_origin_nodes_traffic(
                            o_node.split(","),
                            _regular_traffic,
                            _equity_traffic,
                            _priority_traffic,
                            count_destination_nodes,
                            any(equity_data),
                        )
                    else:
                        _regular_traffic *= self._get_node_traffic(
                            o_node, "values", count_destination_nodes
                        )
                        if any(equity_data):
                            _priority_traffic *= self._get_node_traffic(
                                o_node, "values_prioritarian", count_destination_nodes
                            )
                    if "," in d_node:
                        d_num = len(d_node.split(","))
                        _equity_traffic *= d_num
                        _regular_traffic *= d_num
                        if _equity_traffic_data.with_equity:
                            _priority_traffic *= d_num

                    _equity_traffic_data.update_traffic_routes(
                        _nodes_key_name,
                        _regular_traffic,
                        _equity_traffic,
                        _priority_traffic,
                    )

        return _equity_traffic_data.get_route_traffic(
            _equity_traffic_data._visited_nodes
        )
