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

import logging
from ast import literal_eval
from collections import defaultdict
from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect, AnalysisConfigData,
)
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.analysis.indirect.single_link_redundancy import SingleLinkRedundancy
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum
from ra2ce.network.network_config_data.network_config_data import NetworkSection


def _load_df_from_csv(
        csv_path: Path,
        columns_to_interpret: list[str],
        index: Optional[str | None],
        sep: str = ",",
) -> pd.DataFrame:
    if csv_path is None or not csv_path.exists():
        logging.warning("No `csv` file found at {}.".format(csv_path))
        return pd.DataFrame()

    _csv_dataframe = pd.read_csv(csv_path, sep=sep, on_bad_lines='skip')
    if "geometry" in _csv_dataframe.columns:
        raise Exception(f"The csv file in {csv_path} should not have a geometry column")

    if any(columns_to_interpret):
        _csv_dataframe[columns_to_interpret] = _csv_dataframe[
            columns_to_interpret
        ].applymap(literal_eval)
    if index:
        _csv_dataframe.set_index(index, inplace=True)
    return _csv_dataframe


class Losses(AnalysisIndirectProtocol):
    network: NetworkSection
    graph_file: GraphFile
    analysis: AnalysisSectionIndirect
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames
    result: GeoDataFrame

    def __init__(
            self,
            network_config_data: AnalysisConfigData,
            graph_file: GraphFile,
            analysis: AnalysisSectionIndirect,
            input_path: Path,
            static_path: Path,
            output_path: Path,
            hazard_names: HazardNames,
    ) -> None:
        # TODO: make sure the "link_id" is kept in the result of the criticality analysis
        self.graph_file = graph_file
        self.analysis = analysis
        self.network_config_data = network_config_data
        self.link_id = self.network_config_data.network.file_id
        self.link_type_column = self.network_config_data.network.link_type_column
        self.trip_purposes = self.analysis.trip_purposes

        self.performance_metric = f'diff_{self.analysis.weighing}'

        self.part_of_day: PartOfDayEnum = analysis.part_of_day
        self.analysis_type = analysis.analysis
        self.duration_event: float = analysis.duration_event

        self.intensities = _load_df_from_csv(
            self.analysis.traffic_intensities_file, [], self.link_id)  # per day
        self.resilience_curve = _load_df_from_csv(analysis.resilience_curve_file,
                                                  ["duration_steps",
                                                   "functionality_loss_ratio"], None, sep=";"
                                                  )
        self.values_of_time = _load_df_from_csv(analysis.values_of_time_file, [], None, sep=";")
        self.vot_intensity_per_trip_collection = self._get_vot_intensity_per_trip_purpose()
        self._check_validity_df()

        self.input_path = input_path
        self.static_path = static_path
        self.output_path = output_path
        self.hazard_names = hazard_names

        self.result = gpd.GeoDataFrame()

    def _check_validity_df(self):
        """
        Check spelling of the required input csv files. If user writes wrong spelling, it will raise an error
        when initializing the class.
        """
        _required_values_of_time_keys = ["trip_types", "value_of_time", "occupants"]
        if len(self.values_of_time) > 0 and not all(
                key in self.values_of_time.columns for key in _required_values_of_time_keys):
            raise ValueError(f"Missing required columns in values_of_time: {_required_values_of_time_keys}")

        _required_resilience_curve_keys = ["link_type_hazard_intensity", "duration_steps", "functionality_loss_ratio"]
        if len(self.resilience_curve) > 0 and not all(
                key in self.resilience_curve.columns for key in _required_resilience_curve_keys):
            raise ValueError(f"Missing required columns in resilience_curve: {_required_resilience_curve_keys}")

        if self.link_id not in self.intensities.columns and self.link_id not in self.intensities.index.name:
            raise Exception(f'''traffic_intensities_file and input graph do not have the same link_id.
        {self.link_id} is passed for feature ids of the graph''')

    def _load_gdf(self, gdf_path: Path) -> gpd.GeoDataFrame:
        """This method reads the dataframe created from a .csv"""
        if gdf_path.exists():
            return gpd.read_file(gdf_path, index_col=f"{self.link_id}")
        logging.warning("No `gdf` file found at {}.".format(gdf_path))
        return gpd.GeoDataFrame()

    def _get_vot_intensity_per_trip_purpose(
            self
    ) -> dict[str, pd.DataFrame]:
        """
        Generates a dictionary with all available `vot_purpose` with their intensity as a `pd.DataFrame`.
        """
        _vot_dict = defaultdict(pd.DataFrame)
        for purpose in self.trip_purposes:
            vot_var_name = f"vot_{purpose}"
            partofday_trip_purpose_name = f"{self.part_of_day}_{purpose}"
            partofday_trip_purpose_intensity_name = (
                    "intensity_" + partofday_trip_purpose_name
            )
            # read and set the vot's
            _vot_dict[vot_var_name] = self.values_of_time.loc[
                self.values_of_time["trip_types"] == purpose.config_value, "value_of_time"
            ].item()
            # read and set the intensities
            _vot_dict[partofday_trip_purpose_intensity_name] = (
                    self.intensities[partofday_trip_purpose_name] / 10
                # TODO: Make a new PR to support different time scales: here 10=10hours
            )
        return dict(_vot_dict)

    def calc_vlh(self, criticality_analysis: GeoDataFrame) -> pd.DataFrame:
        def _check_validity_criticality_analysis():
            if self.link_type_column not in criticality_analysis.columns:
                raise Exception(f'''criticality_analysis results does not have the passed link_type_column.
            {self.link_type_column} is passed as link_type_column''')

        def _get_range(height: float) -> str:
            for range_tuple in _hazard_intensity_ranges:
                x, y = range_tuple
                if x <= height <= y:
                    return f"{x}-{y}"
            raise ValueError(f"No matching range found for height {height}")

        criticality_analysis.set_index(self.link_id, inplace=True)
        _check_validity_criticality_analysis()
        _hazard_intensity_ranges = self._get_link_types_heights_ranges()[1]

        # shape vlh
        vlh = pd.DataFrame(
            index=self.intensities.index
        )

        criticality_analysis["EV1_ma"] = 1.2  # ToDO: replace with the HazardOverlay results in the graph_file
        criticality_analysis["EV1_fr"] = 0.1
        events = criticality_analysis.filter(regex=r'^EV(?!1_fr)')
        # Read the performance_change stating the functionality drop
        performance_change = criticality_analysis[self.performance_metric]

        # find the link_type and the hazard intensity
        vlh = pd.merge(
            vlh,
            criticality_analysis[[f"{self.link_type_column}"] + list(events.columns)],
            left_index=True,
            right_index=True,
        )
        for event in events.columns.tolist():
            for _, vlh_row in vlh.iterrows():
                row_hazard_range = _get_range(vlh_row[event])
                row_performance_change = performance_change.loc[vlh_row.name]
                self._populate_vlh_df(vlh, row_hazard_range, vlh_row, row_performance_change, event)

        return vlh

    def _populate_vlh_df(self, vlh: pd.DataFrame, row_hazard_range: str, vlh_row: pd.Series,
                         performance_change, hazard_col_name: str):

        vlh_total = 0

        link_type_hazard_range = (
            f"{vlh_row['link_type']}_{row_hazard_range}"
        )

        # get stepwise recovery curve data
        relevant_curve = self.resilience_curve[
            self.resilience_curve["link_type_hazard_intensity"]
            == link_type_hazard_range
            ]
        if relevant_curve.size == 0:
            raise Exception(f"""{link_type_hazard_range} was not found in the introduced resilience_curve""")
        duration_steps: list = relevant_curve["duration_steps"].item()
        functionality_loss_ratios: list = relevant_curve[
            "functionality_loss_ratio"
        ].item()

        # get vlh_trip_type_event
        for trip_type in self.trip_purposes:
            intensity_trip_type = self.vot_intensity_per_trip_collection[
                f"intensity_{self.part_of_day}_{trip_type}"
            ].loc[vlh_row.name]

            vot_trip_type = float(self.vot_intensity_per_trip_collection[
                                      f"vot_{trip_type}"
                                  ])

            vlh_trip_type_event = sum(
                    intensity_trip_type * duration * loss_ratio * performance_change * vot_trip_type
                    for duration, loss_ratio in zip(
                        duration_steps, functionality_loss_ratios
                    )
                )
            vlh.loc[vlh_row.name, f"vlh_{trip_type}_{hazard_col_name}"] = vlh_trip_type_event
            vlh_total += vlh_trip_type_event
        vlh.loc[vlh_row.name, f"vlh_{hazard_col_name}_total"] = vlh_total

    def calculate_losses_from_table(self) -> pd.DataFrame:
        """
        This function opens an existing table with traffic data and value of time to calculate losses based on
        detouring values. It also includes a traffic jam estimation.
        """
        vlh = self.calc_vlh(criticality_analysis=gpd.GeoDataFrame())
        return vlh

    def _get_link_types_heights_ranges(self) -> tuple[list[str], list[tuple]]:
        _link_types = set()
        _hazard_intensity_ranges = set()

        for entry in self.resilience_curve["link_type_hazard_intensity"]:
            if pd.notna(entry):
                _parts = entry.split("_")
                _link_type = [
                    part
                    for part in _parts
                    if all(isinstance(char, str) for char in part)
                ][0]

                _ranges = [
                    part
                    for part in _parts
                    if any(char.isdigit() or char == "." for char in part)
                ][0]

                _range_parts = _ranges.split("-")
                # Handle the case where the second part is empty, motorway-1.5_ => height > 1.5
                if len(_range_parts) == 1:
                    _range_parts.append("")

                _hazard_range = tuple(float(part) for part in _range_parts)

                _link_types.add(_link_type)
                _hazard_intensity_ranges.add(_hazard_range)

        return list(_link_types), list(_hazard_intensity_ranges)

    def execute(self) -> pd.DataFrame:
        criticality_analysis = SingleLinkRedundancy(
            self.graph_file,
            self.analysis,
            self.input_path,
            self.static_path,
            self.output_path,
            self.hazard_names,
        ).execute()

        self.result = self.calc_vlh(criticality_analysis=criticality_analysis)

        return self.result
