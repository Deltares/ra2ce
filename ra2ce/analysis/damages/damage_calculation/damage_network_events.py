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
from __future__ import annotations

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.damages.damage_calculation.damage_network_base import (
    DamageNetworkBase,
)


class DamageNetworkEvents(DamageNetworkBase):
    """A road network gdf with EVENT-BASED hazard data stored in it, and for which damages can be calculated

    @Author: Kees van Ginkel

    Mandatory attributes:
        *self.events* (set)  : all available unique events
        *self.stats* (set)   : the available statistics
    """

    def __init__(
        self,
        road_gdf: GeoDataFrame,
        val_cols: list[str],
        representative_damage_percentage: float,
    ):
        # Construct using the parent class __init__
        super().__init__(road_gdf, val_cols, representative_damage_percentage)
        self.events = set([x.split("_")[1] for x in val_cols])  # set of unique events

        if not any(self.events):
            raise ValueError("No event cols present in hazard data")

    ### Controler for Event-based damage calculation
    def main(self, damage_function: DamageCurveEnum, manual_damage_functions=None):
        assert len(self.events) > 0, "no return periods identified"
        assert "me" in self.stats, "mean water depth (key: me) is missing"
        assert "fr" in self.stats, "inundated fraction (key: fr) is missing"

        self.do_cleanup_and_mask_creation()

        if damage_function == DamageCurveEnum.HZ:
            self.calculate_damage_HZ(events=self.events)

        if damage_function == DamageCurveEnum.OSD:
            self.calculate_damage_OSdaMage(events=self.events)

        if damage_function == DamageCurveEnum.MAN:
            self.calculate_damage_manual_functions(
                events=self.events, manual_damage_functions=manual_damage_functions
            )


# class DamageNetworkEventsBuilder:
#     @staticmethod
#     def from_csv_file(file_path) -> DamageNetworkEvents:
#         pass
#
#     @staticmethod
#     def from_pandas(pd_dataframe) -> DamageNetworkEvents:
#         pass
