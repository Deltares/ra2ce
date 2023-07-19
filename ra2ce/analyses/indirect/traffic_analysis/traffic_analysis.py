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
import operator
from typing import Any
import numpy as np
import pandas as pd
import geopandas as gpd
import ast
from ra2ce.analyses.indirect.traffic_analysis.accumulated_traffic_dataclass import (
    AccumulatedTaffic,
)
from ra2ce.analyses.indirect.traffic_analysis.traffic_analysis_base import (
    TrafficAnalysisBase,
)

from ra2ce.analyses.indirect.traffic_analysis.traffic_data_wrapper import (
    TrafficDataWrapper,
)


class TrafficAnalysis(TrafficAnalysisBase):
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

    def _get_traffic_data_wrapper(self) -> TrafficDataWrapper:
        _data_wrapper = TrafficDataWrapper()
        _data_wrapper.with_equity = False
        return _data_wrapper

    def _get_accumulated_traffic_from_node(
        self, o_node: str, total_d_nodes: int
    ) -> AccumulatedTaffic:
        _accumulated_traffic = AccumulatedTaffic()
        _accumulated_traffic.regular = self._get_recorded_traffic_in_node(
            o_node, "values", total_d_nodes
        )
        return _accumulated_traffic
