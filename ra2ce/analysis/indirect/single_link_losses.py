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

import geopandas as gpd
import pandas as pd
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_indirect_enum import AnalysisIndirectEnum
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.analysis.indirect.single_link_redundancy import SingleLinkRedundancy
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum
from ra2ce.network.network_config_data.network_config_data import NetworkSection


class SingleLinkLosses(AnalysisIndirectProtocol):
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
            network: NetworkSection,
            graph_file: GraphFile,
            analysis: AnalysisSectionIndirect,
            input_path: Path,
            static_path: Path,
            output_path: Path,
            hazard_names: HazardNames,
    ) -> None:
        # TODO: make sure the "link_id" is kept in the result of the criticality analysis
        # TODO: Enable performing analysis for multiple input networks
        if len(network.primary_file) > 1:
            raise NotImplementedError('A list of networks is not supported yet')
        self.network = network
        self.graph_file = graph_file
        self.analysis = analysis
        self.performance_metric = f'diff_{self.analysis.weighing}'

        self.part_of_day: PartOfDayEnum = analysis.part_of_day
        self.analysis_type = analysis.analysis
        self.duration_event: float = analysis.duration_event

        self.intensities = self._load_df_from_csv(analysis.traffic_intensities_file, [])  # per day
        self.resilience_curve = self._load_df_from_csv(analysis.resilience_curve_file,
                                                       ["duration_steps",
                                                        "functionality_loss_ratio"], sep=";"
                                                       )
        self.values_of_time = self._load_df_from_csv(analysis.values_of_time_file, [], sep=";")
        self._check_validity_df()

        self.criticality_analysis = gpd.GeoDataFrame()

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

    def _load_df_from_csv(
            self,
            csv_path: Path,
            columns_to_interpret: list[str],
            sep: str = ",",
    ) -> pd.DataFrame:
        if csv_path is None or not csv_path.exists():
            logging.warning("No `csv` file found at {}.".format(csv_path))
            return pd.DataFrame()

        _csv_dataframe = pd.read_csv(csv_path, sep=sep, on_bad_lines='skip')
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
            partofday_trip_purpose_name = f"{self.part_of_day.config_value}_{purpose}"
            partofday_trip_purpose_intensity_name = (
                    "intensity_" + partofday_trip_purpose_name
            )
            # read and set the vot's
            _vot_dict[vot_var_name] = self.values_of_time.loc[
                self.values_of_time["trip_types"] == purpose, "value_of_time"
            ].item()
            # read and set the intensities
            _vot_dict[partofday_trip_purpose_intensity_name] = (
                    self.intensities[partofday_trip_purpose_name] / 10
                # TODO: Make a new PR to support different time scales: here 10=10hours
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
            index=self.intensities.link_id,  # "link_type"
        )
        events = self.criticality_analysis.filter(regex="^EV")
        # Read the performance_change stating the functionality drop
        performance_change = self.criticality_analysis[self.performance_metric]

        # find the link_type and the hazard intensity
        vlh = pd.merge(
            vlh,
            self.network[["link_id", "link_type"]],
            left_index=True,
            right_on="link_id",
        )

        if self.analysis_type == AnalysisIndirectEnum.MULTI_LINK_LOSSES:  # only useful for MULTI_LINK_LOSSES
            vlh = pd.merge(
                vlh,
                self.criticality_analysis[["link_id"] + list(events.columns)],
                left_index=True,
                right_on="link_id",
            )

        # for each link and for each event calculate vlh
        for _, vlh_row in vlh.iterrows():
            if self.analysis_type == AnalysisIndirectEnum.SINGLE_LINK_LOSSES:

                row_hazard_range_list = self.resilience_curve['link_type_hazard_intensity'].str.extract(
                    r'_(\d+\.\d+)_(\d+\.\d+)', expand=True).apply(lambda x: '_'.join(x), axis=1).tolist()
                for row_hazard_range in row_hazard_range_list:
                    self._populate_vlh_df(vlh, row_hazard_range, vlh_row, performance_change,
                                          row_hazard_range)


            elif self.analysis_type == AnalysisIndirectEnum.MULTI_LINK_LOSSES:
                for event in events:
                    row_hazard_range = _get_range(vlh_row[event])
                    self._populate_vlh_df(vlh, row_hazard_range, vlh_row, performance_change, event)

            else:
                raise ValueError(f"Invalid analysis type: {self.analysis_type}")

        return vlh

    def _populate_vlh_df(self, vlh: pd.DataFrame, row_hazard_range: str, vlh_row: pd.Series,
                         performance_change, hazard_col_name: str):

        vlh_total = 0
        _trip_types = ["business", "commute", "freight",
                       "other"]  # TODO code smell: this should be either a Enum or read from csv (make a new PR)

        _vot_intensity_per_trip_collection = self._get_vot_intensity_per_trip_purpose(
            _trip_types
        )

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
                f"intensity_{self.part_of_day}_{trip_type}"
            ]

            vot_trip_type = _vot_intensity_per_trip_collection[
                f"vot_{trip_type}"
            ]

            vlh_trip_type_event = sum(
                intensity_trip_type * duration * loss_ratio * performance_change * vot_trip_type
                for duration, loss_ratio in zip(
                    duration_steps, functionality_loss_ratios
                )
            )

            vlh[f"vlh_{trip_type}_{hazard_col_name}"] = vlh_trip_type_event
            vlh_total += vlh_trip_type_event
        vlh[f"vlh_{hazard_col_name}_total"] = vlh_total

    def calculate_losses_from_table(self) -> pd.DataFrame:
        """
        This function opens an existing table with traffic data and value of time to calculate losses based on
        detouring values. It also includes a traffic jam estimation.
        """
        vlh = self.calc_vlh()
        return vlh

    def _get_link_types_heights_ranges(self) -> tuple[list[str], list[tuple]]:
        _link_types = set()
        _hazard_intensity_ranges = set()

        for entry in self.resilience_curve["link_type_hazard_intensity"]:
            if pd.notna(entry):
                _parts = entry.split("_")

                _link_type_parts = [
                    part for part in _parts if not any(char.isdigit() for char in part)
                ]
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
        self.criticality_analysis = SingleLinkRedundancy(
            self.graph_file,
            self.analysis,
            self.input_path,
            self.static_path,
            self.output_path,
            self.hazard_names,
        ).execute()

        _single_link_losses = SingleLinkLosses(
            network=self.network,
            graph_file=GraphFile(),
            analysis=self.analysis,
            input_path=Path(),
            static_path=Path(),
            output_path=Path(),
            hazard_names=HazardNames(names_df=pd.DataFrame())
        )

        self.result = _single_link_losses.calc_vlh()

        return self.result
