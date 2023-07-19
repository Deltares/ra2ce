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
import numpy as np
from ra2ce.analyses.indirect.traffic_analysis.accumulated_traffic_dataclass import (
    AccumulatedTaffic,
)
from ra2ce.analyses.indirect.traffic_analysis.traffic_analysis_base import (
    TrafficAnalysisBase,
)

from ra2ce.analyses.indirect.traffic_analysis.traffic_data_wrapper import (
    TrafficDataWrapper,
)


class EquityAnalysis(TrafficAnalysisBase):
    """
    Specialization from `TrafficAnalysisBase` which takes into account the equity data (weights per region).
    """

    gdf: gpd.GeoDataFrame
    od_table: gpd.GeoDataFrame
    equity_data: pd.DataFrame
    destinations_names: str

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        od_table: gpd.GeoDataFrame,
        destination_names: str,
        equity_data: pd.DataFrame,
    ) -> None:
        self.gdf = gdf
        self.od_table = od_table
        self.destinations_names = destination_names
        self.equity_data = equity_data
        self._set_values_prioritarian(self.equity_data, self.od_table)

    def _set_values_prioritarian(
        self, equity_data: pd.DataFrame, od_table_data: gpd.GeoDataFrame
    ) -> np.array:
        prioritarian_mapping = dict(zip(equity_data["region"], equity_data["weight"]))
        prioritarian_mapping.update({"Not assigned": 1})
        self.od_table["values_prioritarian"] = (
            od_table_data["region"].map(prioritarian_mapping) * od_table_data["values"]
        )

    def _get_traffic_data_wrapper(self) -> TrafficDataWrapper:
        _data_wrapper = TrafficDataWrapper()
        _data_wrapper.with_equity = True
        return _data_wrapper

    def _get_accumulated_traffic_from_node(
        self, o_node: str, total_d_nodes: int
    ) -> AccumulatedTaffic:
        _accumulated_traffic = AccumulatedTaffic()
        _accumulated_traffic.regular = self._get_recorded_traffic_in_node(
            o_node, "values", total_d_nodes
        )
        _accumulated_traffic.prioritarian = self._get_recorded_traffic_in_node(
            o_node, "values_prioritarian", total_d_nodes
        )
        return _accumulated_traffic
