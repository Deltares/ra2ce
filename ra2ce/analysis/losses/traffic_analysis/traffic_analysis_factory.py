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

from pathlib import Path

import geopandas as gpd
import pandas as pd

from ra2ce.analysis.losses.traffic_analysis.equity_analysis import EquityAnalysis
from ra2ce.analysis.losses.traffic_analysis.traffic_analysis import TrafficAnalysis
from ra2ce.analysis.losses.traffic_analysis.traffic_analysis_base import (
    TrafficAnalysisBase,
)


class TrafficAnalysisFactory:
    @staticmethod
    def get_analysis(
        road_network: gpd.GeoDataFrame,
        od_table: gpd.GeoDataFrame,
        destination_names: str,
        equity_data: pd.DataFrame,
    ) -> TrafficAnalysisBase:
        """
        Gets an instance of an `TrafficAnalysisBase` based on whether `equity_data` is provided or not.

        Args:
            road_network (gpd.GeoDataFrame): General dataframe for the road network to analyze.
            od_table (gpd.GeoDataFrame): Origins - destination table dataframe.
            destination_names (str): Destination names.
            equity_data (pd.DataFrame): Dataframe contaning region - weight information.

        Returns:
            TrafficAnalysisBase: Object to make an equity analysis.
        """
        if isinstance(equity_data, pd.DataFrame) and not equity_data.empty:
            return EquityAnalysis(
                road_network, od_table, destination_names, equity_data
            )
        return TrafficAnalysis(road_network, od_table, destination_names)

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
