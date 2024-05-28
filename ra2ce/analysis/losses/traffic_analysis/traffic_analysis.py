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

import geopandas as gpd
import pandas as pd

from ra2ce.analysis.losses.traffic_analysis.accumulated_traffic_dataclass import (
    AccumulatedTraffic,
)
from ra2ce.analysis.losses.traffic_analysis.traffic_analysis_base import (
    TrafficAnalysisBase,
)


class TrafficAnalysis(TrafficAnalysisBase):
    road_network: gpd.GeoDataFrame
    od_table: gpd.GeoDataFrame
    destinations_names: str

    def __init__(
        self,
        road_network: gpd.GeoDataFrame,
        od_table: gpd.GeoDataFrame,
        destination_names: str,
    ) -> None:
        """
        Args:
            road_network (gpd.GeoDataFrame): Geodataframe containing the overall network information.
            od_table (gpd.GeoDataFrame): GeoDataFrame representing the Origins - Destinations table.
            destination_names (str): Destination nodes.
        """
        self.road_network = road_network
        self.od_table = od_table
        self.destinations_names = destination_names

    def _get_accumulated_traffic_from_node(
        self, o_node: str, total_d_nodes: int
    ) -> AccumulatedTraffic:
        _accumulated_traffic = AccumulatedTraffic(egalitarian=1)
        _accumulated_traffic.utilitarian = self._get_recorded_traffic_in_node(
            o_node, "values", total_d_nodes
        )
        return _accumulated_traffic

    def _get_route_traffic(
        self, traffic_data: dict[str, AccumulatedTraffic]
    ) -> pd.DataFrame:
        def convert_to_df(dict_item: tuple[str, AccumulatedTraffic]):
            node_id, traffic_values = dict_item
            u_node, v_node = self._get_key_nodes(node_id)
            return (
                u_node,
                v_node,
                traffic_values.utilitarian,
                traffic_values.egalitarian,
            )

        return pd.DataFrame(
            map(convert_to_df, traffic_data.items()),
            columns=[
                "u",
                "v",
                "traffic",
                "traffic_egalitarian",
            ],
        )
