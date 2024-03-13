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
from collections import defaultdict
import logging

from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionIndirect,
)
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum


class Losses:
    def __init__(self, config: AnalysisConfigData, analysis: AnalysisSectionIndirect):
        self.losses_input_path: Path = config.input_path.joinpath("losses")
        self.duration_event: float = analysis.duration_event
        self.partofday: PartOfDayEnum = analysis.partofday
        self.performance_metric = analysis.performance_metric

        # Load Dataframes
        self.network = self._load_gdf(
            self.losses_input_path.joinpath("network.geojson")
        )
        self.intensities = self._load_df_from_csv(analysis.traffic_intensities_file, [])  # per day

        # TODO: make sure the "link_id" is kept in the result of the criticality analysis
        self.criticality_data = self._load_df_from_csv(Path("criticality_data.csv"), [])
        self.resilience_curve = self._load_df_from_csv(analysis.resilience_curve_file,
                                                       ["disruption_steps", "functionality_loss_ratio",
                                                        "link_type_hazard_intensity"],
                                                       )
        self.values_of_time = self._load_df_from_csv(analysis.values_of_time_file, [])

    def _load_df_from_csv(
            self,
            csv_path: Path,
            columns_to_interpret: list[str],
    ) -> pd.DataFrame:
        if csv_path is None or not csv_path.exists():
            logging.warning("No `csv` file found at {}.".format(csv_path))
            return pd.DataFrame()

        _csv_dataframe = pd.read_csv(csv_path)
        if any(columns_to_interpret):
            _csv_dataframe[columns_to_interpret] = _csv_dataframe[
                columns_to_interpret
            ].applymap(literal_eval)
        return _csv_dataframe

    def _load_gdf(self, gdf_path: Path) -> gpd.GeoDataFrame:
        """This method reads the dataframe created from a .csv"""
        if gdf_path.exists():
            return gpd.read_file(gdf_path, index_col="link_id")
        logging.warning("No `gdf` file found at {}.".format(gdf_path))
        return gpd.GeoDataFrame()

    def _get_vot_intensity_per_trip_purpose(
            self, trip_types: list[str]
    ) -> dict[str, pd.DataFrame]:
        """
        Generates a dictionary with all available `vot_purpose` with their intensity as a `pd.DataFrame`.
        """
        _vot_dict = defaultdict(pd.DataFrame)
        for purpose in trip_types:
            vot_var_name = f"vot_{purpose}"
            partofday_trip_purpose_name = f"{self.partofday.config_value}_{purpose}"
            partofday_trip_purpose_intensity_name = (
                    "intensity_" + partofday_trip_purpose_name
            )
            # read and set the vot's
            _vot_dict[vot_var_name] = self.values_of_time.loc[
                self.values_of_time["trip_types"] == purpose, "value_of_time"
            ].item()
            # read and set the intensities
            _vot_dict[partofday_trip_purpose_intensity_name] = (
                    self.intensities[partofday_trip_purpose_name] / 24
            )
        return dict(_vot_dict)

    def calc_vlh(self) -> pd.DataFrame:
        _link_types_heights_ranges = self._get_link_types_heights_ranges()
        _hazard_intensity_ranges = _link_types_heights_ranges[1]

        def _get_range(height: float) -> str:
            for range_tuple in _hazard_intensity_ranges:
                x, y = range_tuple
                if x <= height <= y:
                    return f"{x}_{y}"
            raise ValueError(f"No matching range found for height {height}")

        # shape vlh
        vlh = pd.DataFrame(
            index=self.intensities.index,  # "link_type"
        )
        events = self.criticality_data.filter(regex="^EV")
        # Read the performance_change stating the functionality drop
        performance_change = self.criticality_data[self.performance_metric]

        # find the link_type and the hazard intensity
        vlh = pd.merge(
            vlh,
            self.network[["link_id", "link_type"]],
            left_index=True,
            right_on="link_id",
        )
        vlh = pd.merge(
            vlh,
            self.criticality_data[["link_id"] + list(events.columns)],
            left_index=True,
            right_on="link_id",
        )

        # set vot values for trip_types
        _trip_types = ["business" "commute" "freight" "other"]
        _vot_intensity_per_trip_collection = self._get_vot_intensity_per_trip_purpose(
            _trip_types
        )

        # for each link and for each event calculate vlh
        for link_id, vlh_row in vlh.iterrows():
            for event in events:
                vlh_event_total = 0
                row_hazard_range = _get_range(vlh_row[event])
                link_type_hazard_range = (
                    f"{vlh_row['link_type']}_{row_hazard_range}"
                )

                # get stepwise recovery curve data
                relevant_curve = self.resilience_curve[
                    self.resilience_curve["link_type_hazard_intensity"]
                    == link_type_hazard_range
                    ]
                duration_steps: list = relevant_curve["duration_steps"].item()
                functionality_loss_ratios: list = relevant_curve[
                    "functionality_loss_ratio"
                ].item()

                # get vlh_trip_type_event
                for trip_type in _trip_types:
                    intensity_trip_type = _vot_intensity_per_trip_collection[
                        f"intensity_{trip_type}"
                    ]
                    vlh_trip_type_event = sum(
                        intensity_trip_type * duration * loss_ratio * performance_change
                        for duration, loss_ratio in zip(
                            duration_steps, functionality_loss_ratios
                        )
                    )

                    vlh[f"vlh_{trip_type}_{event}"] = vlh_trip_type_event
                    vlh_event_total += vlh_trip_type_event
                vlh[f"vlh_{event}_total"] = vlh_event_total

        return vlh

    def calculate_losses_from_table(self) -> pd.DataFrame:
        """
        This function opens an existing table with traffic data and value of time to calculate losses based on
        detouring values. It also includes a traffic jam estimation.
        """
        vlh = self.calc_vlh()
        return vlh

    def _get_link_types_heights_ranges(self) -> tuple[list, pd.DataFrame]:
        _link_types = set()
        _hazard_intensity_ranges = set()

        for entry in self.resilience_curve["link_type_hazard_intensity"]:
            if pd.notna(entry):
                _parts = entry.split("_")

                _link_type_parts = [
                    part for part in _parts if not any(char.isdigit() for char in part)
                ]
                _link_type = "_".join(_link_type_parts)

                _range_parts = [
                    part
                    for part in _parts
                    if any(char.isdigit() or char == "." for char in part)
                ]

                # Handle the case where the second part is empty, motorway_1.5_ => height > 1.5
                if len(_range_parts) == 1:
                    _range_parts.append("")

                _hazard_range = tuple(float(part) for part in _range_parts)

                _link_types.add(_link_type)
                _hazard_intensity_ranges.add(_hazard_range)
        return list(_link_types), list(_hazard_intensity_ranges)
