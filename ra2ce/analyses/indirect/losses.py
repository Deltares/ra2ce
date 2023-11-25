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

import numpy as np
import pandas as pd
import geopandas as gpd

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionIndirect,
)

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
        self.performance_metric = analysis.performance
        self.network: gpd.GeoDataFrame = self.load_gdf(self.losses_input_path, "network.geojson")
        self.intensities = self.load_df_from_csv(self.losses_input_path, "traffic_intensities.csv")  # per day
        # ToDo: make sure the "link_id" is kept in the result of the criticality analysis
        self.criticality_data = self.load_df_from_csv(self.losses_input_path, "criticality_data.csv")
        self.resilience_curve: pd.DataFrame = self.load_df_from_csv(self.losses_input_path,
                                                                    analysis.resilience_curve_file,
                                                                    columns_to_interpret=["disruption_steps",
                                                                                          "functionality_loss_ratio"])
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

        def _set_vot_intensity_per_trip_purpose(purposes: list):
            for purpose in purposes:
                vot_var_name = f"vot_{purpose}"
                partofday_trip_purpose_name = self.partofday + f"_{purpose}"
                partofday_trip_purpose_intensity_name = "intensity_" + partofday_trip_purpose_name
                # read and set the vot's
                globals()[vot_var_name] = \
                    self.values_of_time.loc[self.values_of_time["trip_types"] == purpose, "value_of_time"].item()
                # read and set the intensities
                globals()[partofday_trip_purpose_intensity_name] = self.intensities[partofday_trip_purpose_name] / 24
        # shape vlh
        vlh = pd.DataFrame(
            index=self.intensities.index,  # "link_type"
        )
        events = self.criticality_data.filter(regex='^EV')
        # Read the performance_change stating the functionality drop
        performance_change = self.criticality_data[self.performance_metric]

        # find the link_type and the inundation height
        vlh = pd.merge(vlh, self.network[['link_id', 'link_type']], left_index=True, right_on='link_id')
        vlh = pd.merge(vlh, self.criticality_data[['link_id'] + list(events.columns)],
                       left_index=True, right_on='link_id')

        # set vot values for trip_types
        _set_vot_intensity_per_trip_purpose(trip_types)

        # for each link and for each event calculate vlh
        for link_id, vlh_row in vlh.iterrows():
            for event in events:
                vlh_event_total = 0
                row_inundation_range = _get_range(vlh_row[event])
                link_type_inundation_range = f"{vlh_row['link_type']}_{row_inundation_range}"

                # get stepwise recovery curve data
                relevant_curve = self.resilience_curve[
                    self.resilience_curve["link_type_inundation_height"] == link_type_inundation_range
                    ]
                duration_steps: list = relevant_curve["duration_steps"].item()
                functionality_loss_ratios: list = relevant_curve["functionality_loss_ratio"].item()

                # get vlh_trip_type_event
                for trip_type in trip_types:
                    intensity_trip_type = globals().get(f"intensity_{trip_type}")
                    vlh_trip_type_event = sum(
                        intensity_trip_type * duration * loss_ratio * performance_change
                        for duration, loss_ratio in zip(duration_steps, functionality_loss_ratios)
                    )

                    vlh[f"vlh_{trip_type}_{event}"] = vlh_trip_type_event
                    vlh_event_total += vlh_trip_type_event
                vlh[f"vlh_{event}_total"] = vlh_event_total

        return vlh

    def calculate_losses_from_table(self) -> pd.DataFrame:
        """This function opens an existing table with traffic data and value of time to calculate losses based on
        detouring values. It also includes
            a traffic jam estimation.
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

# link_type = ["motorway", "primary", "secondary", "tertiary", "residential", "secondary_unpaved",
#              "tertiary_unpaved", "residential_unpaved", "tunnel", "bridge", "culvert"]

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
