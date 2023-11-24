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
import numpy as np
import pandas as pd

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

    @staticmethod
    def values_of_time(file_path: Path) -> dict:
        """This function is to calculate vehicle loss hours based on an input table
        with value of time per type of transport, usage and value_of_reliability"""
        df_lookup = pd.read_csv(file_path, index_col="transport_type")
        lookup_dict = df_lookup.transpose().to_dict()
        return lookup_dict

    @staticmethod
    def load_df(path: Path, file: str):
        """This method reads the dataframe created from a .csv"""
        file_path = path / file
        df = pd.read_csv(file_path, index_col="link_id")
        return df

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

    def calc_vlh(
            self,
            traffic_data: pd.DataFrame,
            values_of_time: dict,
            criticality_data: pd.DataFrame,
    ) -> pd.DataFrame:

        # TODO: vlh dataframe, the line are all the segments of the road network
        # TODO: we need somehow to loop over all the vehicle types and calculate the vlh for each type(and each segment)

        vlh = pd.DataFrame(
            index=traffic_data.index,
            columns=[
                "",
                "vlh_detour_business",
                "vlh_detour_commute",
                "vlh_detour_freight",
                "vlh_detour_other",
                "vlh_detour",
                "currency_per_hour",
                "currency_vlh",
            ],
        )
        diff_event_disr = self.duration - self.duration_disr

        prefix = partofday_prefixes.get(self.partofday, None)

        if prefix:
            intensity_business = traffic_data[f"{prefix}_business"] / 24
            intensity_commute = traffic_data[f"{prefix}_commute"] / 24
            intensity_freight = traffic_data[f"{prefix}_freight"] / 24
            intensity_other = traffic_data[f"{prefix}_other"] / 24
            intensity_total = traffic_data[f"{prefix}_total"] / 24
        else:
            intensity_business = intensity_commute = intensity_freight = intensity_other = intensity_total = None

        detour_time = criticality_data["diff_time"]

        # vlh = self.traffic_shockwave(vlh, capacity, intensity) vlh["vlh_traffic"]

        # TODO: integration here of time and traffic_throughput.
        # ToDo: differentiate between types of vehicle
        # ToDo: add stepwise event duration and recovery % introduced by the user:
        #  duration = [x, y, z], recovery = [a%, b%, c%]
        for trip_type in trip_types:
            trip_intensity = f"intensity_{trip_type}"
            intensity_column = globals().get(trip_intensity, None)
            if intensity_column is not None:
                vlh[f"vlh_detour_{trip_type}"] = (intensity_column * ((1 - self.traffic_throughput) * self.duration) *
                                                  vlh[f"detour_time_{trip_type}"]) / 60
        duration = get_duration()

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
            vlh["currency_per_hour"] = (
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
            vlh["currency_per_hour"] = (
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
        vlh["currency_vlh"] = vlh["currency_per_hour"] * vlh["vlh_total"]
        return vlh

    def calculate_losses_from_table(self):
        """This function opens an existing table with traffic data and value of time to calculate losses based on detouring values. It also includes
        a traffic jam estimation.
        #TODO: check if gdf already exists from effectiveness measures.
        #TODO: If not: read feather file.
        #TODO: if yes: read gdf
        #TODO: koppelen van VVU aan de directe schade berekeningen
        """
        traffic_data = self.load_df(self.losses_input_path, "traffic_intensities.csv")  # intensities per day
        # relevant traffic_intensities_attributes = [
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

        criticality_data = self.load_df(self.losses_input_path, "criticality_data.csv")
        # relevant criticality_data_attributes = [
        #     "link_id",
        #     "alt_dist", (km)
        #     "alt_time", (hr)
        #     "diff_dist", (km)
        #     "diff_time", (hr)
        # ]

        values_of_time = self.values_of_time(self.losses_input_path / "values_of_time.csv")
        # relevant values_of_time = [
        #     "transport_type",
        #     "value_of_time",
        #     "occupants",
        # ]

        vlh = self.calc_vlh(traffic_data, values_of_time, criticality_data)
        return vlh
