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
from ast import literal_eval
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import geopandas as gpd

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionIndirect,
)

partofday_prefixes = {
    "daily": "day",
    "evening": "evening",
}
trip_types = [
    "business"
    "commute"
    "freight"
    "other"
]

road_types = ["motorway", "primary", "secondary", "tertiary", "residential", "secondary_unpaved",
              "tertiary_unpaved", "residential_unpaved", "tunnel", "bridge", "culvert"]


class Losses:
    def __init__(self, config: AnalysisConfigData, analysis: AnalysisSectionIndirect):
        self.losses_input_path: Path = config.input_path.joinpath("losses")
        self.duration: float = analysis.duration_event
        self.duration_disr: float = analysis.duration_disruption
        self.detour_traffic: float = analysis.fraction_detour
        self.traffic_throughput: float = analysis.fraction_drivethrough
        self.rest_capacity: float = analysis.rest_capacity
        self.maximum: float = analysis.maximum_jam
        self.partofday: str = analysis.partofday
        self.network: gpd.GeoDataFrame = self.load_gdf(self.losses_input_path, "network.geojson")
        self.traffic_data = self.load_df_from_csv(self.losses_input_path, "traffic_intensities.csv")  # per day
        self.criticality_data = self.load_df_from_csv(self.losses_input_path, "criticality_data.csv")
        self.resilience_curve: pd.DataFrame = self.load_df_from_csv(self.losses_input_path,
                                                                    analysis.resilience_curve_file,
                                                                    ["disruption_steps", "functionality_loss_ratio"])
        self.values_of_time = self.load_df_from_csv(self.losses_input_path, "values_of_time.csv", "")
        self.link_types: list = self._get_link_types_heights_ranges()[0]
        self.inundation_height_ranges: pd.DataFrame = self._get_link_types_heights_ranges()[1]

    @staticmethod
    def values_of_time(file_path: Path) -> dict:
        """This function is to calculate vehicle loss hours based on an input table
        with value of time per type of transport, usage and value_of_reliability"""
        df_lookup = pd.read_csv(file_path, index_col="transport_type")
        lookup_dict = df_lookup.transpose().to_dict()
        return lookup_dict

    @staticmethod
    def load_df_from_csv(path: Path, file: str, index_col: str = "", columns_to_interpret=None):
        if columns_to_interpret is None:
            columns_to_interpret = []
        file_path = path / file
        if len(index_col) > 0:
            df = pd.read_csv(file_path, index_col=index_col)
        else:
            df = pd.read_csv(file_path)
        if len(columns_to_interpret) > 0:
            df[columns_to_interpret] = df[columns_to_interpret].applymap(literal_eval)
        return df

    @staticmethod
    def load_gdf(path: Path, file: str):
        """This method reads the dataframe created from a .csv"""
        file_path = path / file
        gdf = gpd.read_file(file_path, index_col="link_id")
        return gdf

    def traffic_shockwave(
            self, vlh: pd.DataFrame, capacity: pd.Series, intensity: pd.Series
    ) -> pd.DataFrame:
        vlh["vlh_traffic"] = (
                (self.duration ** 2)
                * (self.rest_capacity - 1)
                * (self.rest_capacity * capacity - intensity / self.traffic_throughput)
                / (2 * (1 - ((intensity / self.traffic_throughput) / capacity)))
        )
        return vlh

    def calc_vlh_with_shockwave(
            self,
            traffic_data: pd.DataFrame,
            values_of_time: dict,
            criticality_data: pd.DataFrame,
    ) -> pd.DataFrame:

        # TODO: vlh dataframe, the line are all the segments of the road network
        # TODO: we need somehow to loop over all the vehicle types and calculate the vlh for each type (and each segment)

        vlh = pd.DataFrame(
            index=traffic_data.index,
            columns=[
                "vlh_traffic",
                "vlh_detour",
                "vlh_total",
                "euro_per_hour",
                "euro_vlh",
            ],
        )
        capacity = traffic_data["capacity"]
        diff_event_disr = self.duration - self.duration_disr

        if self.partofday == "daily":
            intensity = traffic_data["day_total"] / 24
            detour_time = criticality_data["detour_time_day"]
        if self.partofday == "evening":
            intensity = traffic_data["evening_total"]
            detour_time = criticality_data["detour_time_evening"]

        vlh = self.traffic_shockwave(vlh, capacity, intensity)
        vlh["vlh_traffic"] = vlh["vlh_traffic"].apply(
            lambda x: np.where(x < 0, 0, x)
        )  # all values below 0 -> 0
        vlh["vlh_traffic"] = vlh["vlh_traffic"].apply(
            lambda x: np.where(x > self.maximum, self.maximum, x)
        )
        # all values above maximum, limit to maximum
        # TODO: integration here of time and traffic_throughput.
        vlh["vlh_detour"] = (
                                    intensity * ((1 - self.traffic_throughput) * self.duration) * detour_time
                            ) / 60
        vlh["vlh_detour"] = vlh["vlh_detour"].apply(
            lambda x: np.where(x < 0, 0, x)
        )  # all values below 0 -> 0

        if (
                diff_event_disr > 0
        ):  # when the event is done, but the disruption continues after the event. Calculate extra detour times
            temp = (
                    diff_event_disr * (detour_time * self.detour_traffic * detour_time) / 60
            )
            temp = temp.apply(
                lambda x: np.where(x < 0, 0, x)
            )  # all values below 0 -> 0
            vlh["vlh_detour"] = vlh["vlh_detour"] + temp

        vlh["vlh_total"] = vlh["vlh_traffic"] + vlh["vlh_detour"]

        if self.partofday == "daily":
            vlh["euro_per_hour"] = (
                    (
                            traffic_data["day_freight"]
                            / traffic_data["day_total"]
                            * values_of_time["freight"]["value_of_time"]
                    )
                    + (
                            traffic_data["day_commute"]
                            / traffic_data["day_total"]
                            * values_of_time["commute"]["value_of_time"]
                    )
                    + (
                            traffic_data["day_business"]
                            / traffic_data["day_total"]
                            * values_of_time["business"]["value_of_time"]
                    )
                    + (
                            traffic_data["day_other"]
                            / traffic_data["day_total"]
                            * values_of_time["other"]["value_of_time"]
                    )
            )
            # to calculate costs per unit traffi per hour. This is weighted based on the traffic mix and value of each traffic type

        if self.partofday == "evening":
            vlh["euro_per_hour"] = (
                    (
                            traffic_data["evening_freight"]
                            / traffic_data["evening_total"]
                            * values_of_time["freight"]["value_of_time"]
                    )
                    + (
                            traffic_data["evening_commute"]
                            / traffic_data["evening_total"]
                            * values_of_time["commute"]["value_of_time"]
                    )
                    + (
                            traffic_data["evening_business"]
                            / traffic_data["evening_total"]
                            * values_of_time["business"]["value_of_time"]
                    )
                    + (
                            traffic_data["evening_other"]
                            / traffic_data["evening_total"]
                            * values_of_time["other"]["value_of_time"]
                    )
            )
            # to calculate costs per unit traffi per hour. This is weighted based on the traffic mix and value of each traffic type
        vlh["euro_vlh"] = vlh["euro_per_hour"] * vlh["vlh_total"]
        return vlh

    def calc_vlh(self) -> pd.DataFrame:
        def _get_range(height: float) -> str:
            for range_tuple in self.inundation_height_ranges:
                x, y = range_tuple
                if x <= height <= y:
                    return f"{x}_{y}"
            raise ValueError(f"No matching range found for height {height}")

        # TODO: vlh dataframe, the line are all the segments of the road network
        # TODO: we need somehow to loop over all the vehicle types and calculate the vlh for each type(and each segment)
        # shape vlh
        vlh = pd.DataFrame(
            index=self.traffic_data.index,
            columns=[
                "link_type",
                "inundation_height"
                "vlh_detour_total",
                "currency_per_hour",
                "currency_vlh",
            ],
        )
        vlh_detour_trip_types = [
            "vlh_detour_business",
            "vlh_detour_commute",
            "vlh_detour_freight",
            "vlh_detour_other"
        ]
        events = self.criticality_data.filter(regex='^EV')

        # read the intensities
        partofday_prefix = partofday_prefixes.get(self.partofday, None)
        if partofday_prefix:
            intensity_business = self.traffic_data[f"{partofday_prefix}_business"] / 24
            intensity_commute = self.traffic_data[f"{partofday_prefix}_commute"] / 24
            intensity_freight = self.traffic_data[f"{partofday_prefix}_freight"] / 24
            intensity_other = self.traffic_data[f"{partofday_prefix}_other"] / 24
            intensity_total = self.traffic_data[f"{partofday_prefix}_total"] / 24
        else:
            intensity_business = intensity_commute = intensity_freight = intensity_other = intensity_total = None

        # Read the performance_change stating the functionality drop
        performance_change = self.criticality_data["diff_time"]

        # find the link_type and the inundation height
        vlh = pd.merge(vlh, self.network[['link_id', 'link_type']], left_index=True, right_on='link_id')
        vlh = pd.merge(vlh, self.criticality_data[['link_id'] + list(events.columns)],
                       left_index=True, right_on='link_id')
        for link_id, vlh_row in vlh.iterrows():
            for event in events:
                #  get duration_steps and functionality_loss_ratio from resilience_curve
                row_inundation_range = _get_range(vlh_row[event])
                link_type_inundation_range = vlh_row["link_type"] + "_" + row_inundation_range
                for trip_type in trip_types:
                    variable_name = f"vot_{trip_type}"
                    globals()[variable_name] = \
                        self.values_of_time.loc[self.values_of_time["trip_types"] == trip_type, "value_of_time"].item()

                    trip_intensity = f"intensity_{trip_type}"
                    intensity_column = globals().get(trip_intensity, None)
                    if intensity_column is not None:
                        for vlh_detour_trip_type in vlh_detour_trip_types:
                            vlh_detour_trip_type_event = f"{vlh_detour_trip_type}_{event}"
                        # vlh[vlh_detour_trip_type_event] = (intensity_column * (
                        #             (1 - self.traffic_throughput) * self.duration) *
                        #                                   vlh[f"detour_time_{trip_type}"]) / 60
                        pass

        return vlh

    def calculate_losses_from_table(self):
        """This function opens an existing table with traffic data and value of time to calculate losses based on detouring values. It also includes
        a traffic jam estimation.
        #TODO: check if gdf already exists from effectiveness measures.
        #TODO: If not: read feather file.
        #TODO: if yes: read gdf
        #TODO: koppelen van VVU aan de directe schade berekeningen
        """
        vlh = self.calc_vlh()
        return vlh

    def _get_link_types_heights_ranges(self) -> tuple:
        _link_types = set()
        _inundation_height_ranges = set()

        for entry in self.resilience_curve['link_type_inundation_height']:
            if pd.notna(entry):
                _parts = entry.split('_')

                _link_type_parts = [part for part in _parts if not any(char.isdigit() for char in part)]
                _link_type = '_'.join(_link_type_parts)

                _range_parts = [part for part in _parts if any(char.isdigit() or char == '.' for char in part)]

                # Handle the case where the second part is empty, motorway_1.5_ => height > 1.5
                if len(_range_parts) == 1:
                    _range_parts.append('')

                _inundation_range = tuple(float(part) for part in _range_parts)

                _link_types.add(_link_type)
                _inundation_height_ranges.add(_inundation_range)
        return list(_link_types), list(_inundation_height_ranges)


#  must-have network (.geojson): input road network = [
# "link_id",
# "avgspeed",
# "link_type",
# "geometry",
# ]

link_type = ["motorway", "primary", "secondary", "tertiary", "residential", "secondary_unpaved",
             "tertiary_unpaved", "residential_unpaved", "tunnel", "bridge", "culvert"]

# must-have traffic_intensities attributes = [
#     "link_id"
#     "evening_total",
#     "evening_freight",
#     "evening_commute",
#     "evening_business",
#     "evening_other",
#     "day_freight",
#     "day_commute",
#     "day_business",
#     "day_other",
#     "day_total",
# ]

# must-have values_of_time: ina currency attributes= [
#     "transport_type",
#     "value_of_time",
#     "occupants",
# ]

# ToDo: make sure the "link_id" is kept in the result
# must-have criticality_data attributes = [
#     "link_id",
#     "alt_dist", (km)
#     "alt_time", (hr)
#     "diff_dist", (km)
#     "diff_time", (hr)
# ]

# must-have resilience_curve attributes: total recovery duration is defined in days (by the user) = [
#   link_type_inundation_height	: e.g., motorway_0_0.2 (link_type_inundation_range)
#   duration_steps
#   functionality_loss_steps
# ]
