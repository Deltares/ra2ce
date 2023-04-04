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


import numpy as np
import pandas as pd


class Losses:
    def __init__(self, config, analysis):
        self.config = config
        self.analysis = analysis
        self.duration = analysis["duration_event"]
        self.duration_disr = analysis["duration_disruption"]
        self.detour_traffic = analysis["fraction_detour"]
        self.traffic_throughput = analysis["fraction_drivethrough"]
        self.rest_capacity = analysis["rest_capacity"]
        self.maximum = analysis["maximum_jam"]
        self.partofday = analysis["partofday"]

    @staticmethod
    def vehicle_loss_hours(path):
        """This function is to calculate vehicle loss hours based on an input table
        with value of time per type of transport, usage and value_of_reliability"""

        file_path = path / "vehicle_loss_hours.csv"
        df_lookup = pd.read_csv(file_path, index_col="transport_type")
        lookup_dict = df_lookup.transpose().to_dict()
        return lookup_dict

    @staticmethod
    def load_df(path, file):
        """This method reads the dataframe created from a .csv"""
        file_path = path / file
        df = pd.read_csv(file_path, index_col="LinkNr")
        return df

    def traffic_shockwave(self, vlh: pd.DataFrame, capacity: pd.Series, intensity: pd.Series) -> pd.DataFrame:
        vlh["vlh_traffic"] = (
            (self.duration**2)
            * (self.rest_capacity - 1)
            * (self.rest_capacity * capacity - intensity / self.traffic_throughput)
            / (2 * (1 - ((intensity / self.traffic_throughput) / capacity)))
        )
        return vlh

    def calc_vlh(
        self, traffic_data: pd.DataFrame, vehicle_loss_hours: pd.Series, detour_data: pd.DataFrame
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
            detour_time = detour_data["detour_time_day"]
        if self.partofday == "evening":
            intensity = traffic_data["evening_total"]
            detour_time = detour_data["detour_time_evening"]

        vlh = self.traffic_shockwave(vlh, capacity, intensity)
        vlh["vlh_traffic"] = vlh["vlh_traffic"].apply(
            lambda x: np.where(x < 0, 0, x)
        )  # all values below 0 -> 0
        vlh["vlh_traffic"] = vlh["vlh_traffic"].apply(
            lambda x: np.where(x > self.maximum, self.maximum, x)
        )
        # all values above maximum, limit to maximum
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
                    * vehicle_loss_hours["freight"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["day_commute"]
                    / traffic_data["day_total"]
                    * vehicle_loss_hours["commute"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["day_business"]
                    / traffic_data["day_total"]
                    * vehicle_loss_hours["business"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["day_other"]
                    / traffic_data["day_total"]
                    * vehicle_loss_hours["other"]["vehicle_loss_hour"]
                )
            )
            # to calculate costs per unit traffi per hour. This is weighted based on the traffic mix and value of each traffic type

        if self.partofday == "evening":
            vlh["euro_per_hour"] = (
                (
                    traffic_data["evening_freight"]
                    / traffic_data["evening_total"]
                    * vehicle_loss_hours["freight"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["evening_commute"]
                    / traffic_data["evening_total"]
                    * vehicle_loss_hours["commute"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["evening_business"]
                    / traffic_data["evening_total"]
                    * vehicle_loss_hours["business"]["vehicle_loss_hour"]
                )
                + (
                    traffic_data["evening_other"]
                    / traffic_data["evening_total"]
                    * vehicle_loss_hours["other"]["vehicle_loss_hour"]
                )
            )
            # to calculate costs per unit traffi per hour. This is weighted based on the traffic mix and value of each traffic type
        vlh["euro_vlh"] = vlh["euro_per_hour"] * vlh["vlh_total"]
        return vlh

    def calculate_losses_from_table(self):
        """This function opens an existing table with traffic data and value of time to calculate losses based on detouring values. It also includes
        a traffic jam estimation.
        #TODO: check if gdf already exists from effectiveness measures.
        #TODO: If not: read feather file.
        #TODO: if yes: read gdf
        #TODO: koppelen van VVU aan de directe schade berekeningen
        """

        traffic_data = self.load_df(
            self.config["input"] / "losses", "traffic_intensities.csv"
        )
        dict1 = {
            "AS_VTG": "evening_total",
            "AS_FRGT": "evening_freight",
            "AS_COMM": "evening_commute",
            "AS_BUSS": "evening_business",
            "AS_OTHR": "evening_other",
            "ET_FRGT": "day_freight",
            "ET_COMM": "day_commute",
            "ET_BUSS": "day_business",
            "ET_OTHR": "day_other",
            "ET_VTG": "day_total",
            "afstand": "distance",
            "H_Cap": "capacity",
            "H_Stroken": "lanes",
        }
        traffic_data.rename(columns=dict1, inplace=True)

        detour_data = self.load_df(self.config["input"] / "losses", "detour_data.csv")
        dict2 = {
            "VA_AV_HWN": "detour_time_evening",
            "VA_RD_HWN": "detour_time_remaining",
            "VA_OS_HWN": "detour_time_morning",
            "VA_Etm_HWN": "detour_time_day",
        }
        detour_data.rename(columns=dict2, inplace=True)

        vehicle_loss_hours = self.vehicle_loss_hours(self.config["input"] / "losses")
        vlh = self.calc_vlh(traffic_data, vehicle_loss_hours, detour_data)
        return vlh
