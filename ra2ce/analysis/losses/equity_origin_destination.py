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

from geopandas import GeoDataFrame, read_feather

from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.losses.optimal_route_origin_destination import (
    OptimalRouteOriginDestination,
)
from ra2ce.analysis.losses.traffic_analysis.traffic_analysis_factory import (
    TrafficAnalysisFactory,
)


class EquityOriginDestination(OptimalRouteOriginDestination):

    def execute(self) -> AnalysisResultWrapper:
        gdf = self.optimal_route_origin_destination(
            self.graph_file.get_graph(), self.analysis
        )

        self._save_equity_traffic(gdf)

        return self.generate_result_wrapper(gdf)
    
    def _save_equity_traffic(self, gdf: GeoDataFrame) -> None:
        od_table = read_feather(
            self.static_path.joinpath(
                "output_graph", "origin_destination_table.feather"
            )
        )

        route_traffic_df = self.optimal_route_od_link(
            gdf,
            od_table,
            TrafficAnalysisFactory.read_equity_weights(self.analysis.equity_weight),
        )
        impact_csv_path = self.output_path.joinpath(
            self.analysis.config_name,
            (self.analysis.name.replace(" ", "_") + "_link_traffic.csv"),
        )
        route_traffic_df.to_csv(impact_csv_path, index=False)
