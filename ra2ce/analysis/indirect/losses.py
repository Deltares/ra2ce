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
import ast

import geopandas as gpd
import pandas as pd
import math

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_config_data.enums.trip_purposes import TripPurposeEnum
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.analysis.indirect.single_link_redundancy import SingleLinkRedundancy
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum


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
    analysis: AnalysisSectionIndirect
    graph_file_hazard: GraphFile
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames

    def __init__(self, analysis_input: AnalysisInputWrapper, analysis_config: AnalysisConfigWrapper) -> None:
        self.analysis_input = analysis_input
        self.analysis_config = analysis_config
        self.analysis = self.analysis_input.analysis
        self.graph_file_hazard = self.analysis_input.graph_file_hazard

        self.link_id = analysis_config.config_data.network.file_id
        self.link_type_column = analysis_config.config_data.network.link_type_column
        self.trip_purposes = self.analysis.trip_purposes

        self.performance_metric = f'diff_{self.analysis.weighing}'

        self.part_of_day: PartOfDayEnum = self.analysis.part_of_day
        self.analysis_type = self.analysis.analysis
        self.duration_event: float = self.analysis.duration_event
        self.hours_per_day: float = self.analysis.hours_per_day
        self.production_loss_per_capita_per_hour = (
                self.analysis.production_loss_per_capita_per_day / self.hours_per_day)
        self._check_validity_analysis_files()
        self.intensities = _load_df_from_csv(
            Path(self.analysis.traffic_intensities_file), [], self.link_id)  # per day
        self.resilience_curve = _load_df_from_csv(Path(self.analysis.resilience_curve_file),
                                                  ["duration_steps",
                                                   "functionality_loss_ratio"], None, sep=";"
                                                  )
        self.values_of_time = _load_df_from_csv(Path(self.analysis.values_of_time_file), [], None, sep=";")
        self._check_validity_df()

        self.input_path = self.analysis_input.input_path
        self.static_path = self.analysis_input.static_path
        self.output_path = self.analysis_input.output_path
        self.hazard_names = self.analysis_input.hazard_names

        self.result = gpd.GeoDataFrame()

    def _check_validity_analysis_files(self):
        if (self.analysis.traffic_intensities_file is None or
                self.analysis.resilience_curve_file is None or
                self.analysis.values_of_time_file is None):
            raise ValueError(
                f"traffic_intensities_file, resilience_curve_file, and values_of_time_file should be given")

    def _check_validity_df(self):
        """
        Check spelling of the required input csv files. If user writes wrong spelling, it will raise an error
        when initializing the class.
        """
        _required_values_of_time_keys = ["trip_types", "value_of_time", "occupants"]
        if not all(key in self.values_of_time.columns for key in _required_values_of_time_keys):
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

        for trip_purpose in self.trip_purposes:
            vot_var_name = f"vot_{trip_purpose}"
            occupancy_var_name = f"occupants_{trip_purpose}"
            partofday_trip_purpose_name = f"{self.part_of_day}_{trip_purpose}"
            partofday_trip_purpose_intensity_name = (
                    "intensity_" + partofday_trip_purpose_name
            )
            # read and set the vot's
            _vot_dict[vot_var_name] = self.values_of_time.loc[
                self.values_of_time["trip_types"] == trip_purpose.config_value, "value_of_time"
            ].item()
            _vot_dict[occupancy_var_name] = self.values_of_time.loc[
                self.values_of_time["trip_types"] == trip_purpose.config_value, "occupants"
            ].item()
            # read and set the intensities
            _vot_dict[partofday_trip_purpose_intensity_name] = (
                    self.intensities_simplified_graph[partofday_trip_purpose_name] / self.hours_per_day
            )
        return dict(_vot_dict)

    def _get_disrupted_criticality_analysis_results(self, criticality_analysis: gpd.GeoDataFrame):
        # filter out all links not affected by the hazard
        if self.analysis.aggregate_wl == AggregateWlEnum.NONE:
            self.criticality_analysis = criticality_analysis[criticality_analysis['EV1_ma'] != 0]
        elif self.analysis.aggregate_wl == AggregateWlEnum.MAX:
            self.criticality_analysis = criticality_analysis[criticality_analysis['EV1_max'] != 0]
        elif self.analysis.aggregate_wl == AggregateWlEnum.MEAN:
            self.criticality_analysis = criticality_analysis[criticality_analysis['EV1_mean'] != 0]
        elif self.analysis.aggregate_wl == AggregateWlEnum.MIN:
            self.criticality_analysis = criticality_analysis[criticality_analysis['EV1_min'] != 0]

        self.criticality_analysis_non_disrupted = criticality_analysis[
            ~criticality_analysis.index.isin(self.criticality_analysis.index)
        ]
        # link_id from list to tuple
        if len(self.criticality_analysis_non_disrupted) > 0:
            self.criticality_analysis_non_disrupted[self.link_id] = self.criticality_analysis_non_disrupted[
            self.link_id].apply(lambda x: tuple(x) if isinstance(x, list) else x)
        self.criticality_analysis[self.link_id] = self.criticality_analysis[self.link_id].apply(
            lambda x: tuple(x) if isinstance(x, list) else x)

        self.criticality_analysis.set_index(self.link_id, inplace=True)
        self.criticality_analysis_non_disrupted = self.criticality_analysis_non_disrupted.reset_index()

    def _get_intensities_simplified_graph(self) -> pd.DataFrame:
        _intensities_simplified_graph_list = []

        for index in self.criticality_analysis.index.values:
            if isinstance(index, tuple):
                filtered_intensities = self.intensities[self.intensities.index.isin(index)]

                # Create a new DataFrame with the index set to tuple_of_indices and the maximum values as the values
                max_intensities = filtered_intensities.max().to_frame().T
                max_intensities.index = [index]

                row_data = max_intensities.squeeze()
            else:
                row_data = self.intensities.loc[index]

            _intensities_simplified_graph_list.append(row_data)
        _intensities_simplified_graph = pd.DataFrame(_intensities_simplified_graph_list,
                                                     index=self.criticality_analysis.index.values)
        return _intensities_simplified_graph

    def calculate_vehicle_loss_hours(self) -> gpd.GeoDataFrame:
        """
        This function opens an existing table with traffic data and value of time to calculate losses based on
        detouring values. It also includes a traffic jam estimation.
        """

        def _check_validity_criticality_analysis():
            if self.link_type_column not in self.criticality_analysis.columns:
                raise Exception(f'''criticality_analysis results does not have the passed link_type_column.
            {self.link_type_column} is passed as link_type_column''')

        def _get_range(height: float) -> str:
            for range_tuple in _hazard_intensity_ranges:
                x, y = range_tuple
                if x <= height <= y:
                    return f"{x}-{y}"
            raise ValueError(f"No matching range found for height {height}")

        def _create_result(vlh: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
            result = pd.concat(
                [
                    vlh,
                    self.criticality_analysis_non_disrupted[
                        [f"{self.link_id}", f"{self.link_type_column}", "geometry", f"{self.performance_metric}", "detour"] +
                        list(events.columns)
                        ]
                ]
            )
            result = result.reset_index()

            # Get the columns from vehicle_loss_hours that are not in common
            additional_columns = list(set(vlh.columns) - set(self.criticality_analysis_non_disrupted.columns))

            # Fill 0 for the additional columns of self.criticality_analysis_non_disrupted
            result.loc[result.index.difference(vlh.index), additional_columns] = result.loc[
                result.index.difference(vlh.index), additional_columns].fillna(0)
            return result

        _check_validity_criticality_analysis()
        _hazard_intensity_ranges = self._get_link_types_heights_ranges()[1]
        events = self.criticality_analysis.filter(regex=r'^EV(?!1_fr)')
        # Read the performance_change stating the functionality drop
        performance_change = self.criticality_analysis[self.performance_metric]

        # shape vehicle_loss_hours
        vehicle_loss_hours_df = pd.DataFrame(columns=[self.link_id], data=self.criticality_analysis.index.values)

        # find the link_type and the hazard intensity
        vehicle_loss_hours_df = pd.merge(
            vehicle_loss_hours_df,
            self.criticality_analysis[
                [f"{self.link_type_column}", "geometry", f"{self.performance_metric}", "detour"] + list(events.columns)
                ],
            left_on=self.link_id,
            right_index=True,
        )
        vehicle_loss_hours = gpd.GeoDataFrame(
            vehicle_loss_hours_df, geometry="geometry", crs=self.criticality_analysis.crs)
        for event in events.columns.tolist():
            for _, vlh_row in vehicle_loss_hours.iterrows():
                row_hazard_range = _get_range(vlh_row[event])
                row_performance_change = performance_change.loc[[vlh_row[self.link_id]]]
                if math.isnan(row_performance_change):
                    self._calculate_production_loss_per_capita(vehicle_loss_hours, vlh_row, event)
                else:
                    self._populate_vehicle_loss_hour(vehicle_loss_hours, row_hazard_range, vlh_row,
                                                     row_performance_change, event)

        vehicle_loss_hours_result = _create_result(vehicle_loss_hours)
        return vehicle_loss_hours_result

    def _calculate_production_loss_per_capita(self, vehicle_loss_hours: gpd.GeoDataFrame, vlh_row: pd.Series,
                                              hazard_col_name: str):
        """
        In cases where there is no alternative route in the event of disruption of the road, we propose to use a
        proxy for the assessment of losses from the interruption of services from the road in these cases where no
        alternative routes exist.
        The assumption for the proxy is that a loss of production will occur from the
        interruption of the road, equal to the size of the added value from the persons that cannot make use of the
        road, measured in the regional GDP per capita. This assumption constitutes both the loss of production within
        the area that cannot be reached, as well the loss of production outside the area due to the inability of the
        workers from within the cut-off area to arrive at their place of production outside this area.

        The daily loss of productivity for each link section without detour routes, when they are
        disrupted is then obtained multiplying the traffic intensity by the total occupancy per vehicle type,
        including drivers, by the daily loss of productivity per capita per hour.

        the unit of time is hour.
        """
        vlh_total = 0
        for trip_type in self.trip_purposes:
            intensity_trip_type = self.vot_intensity_per_trip_collection[
                f"intensity_{self.part_of_day}_{trip_type}"
            ].loc[[vlh_row[self.link_id]]]
            occupancy_trip_type = float(self.vot_intensity_per_trip_collection[
                                            f"occupants_{trip_type}"
                                        ])
            vlh_trip_type_event_series = (
                    self.duration_event *
                    intensity_trip_type *
                    occupancy_trip_type *
                    self.production_loss_per_capita_per_hour
            )
            vlh_trip_type_event = vlh_trip_type_event_series.squeeze()
            vehicle_loss_hours.loc[[vlh_row.name], f"vlh_{trip_type}_{hazard_col_name}"] = vlh_trip_type_event
            vlh_total += vlh_trip_type_event
        vehicle_loss_hours.loc[[vlh_row.name], f"vlh_{hazard_col_name}_total"] = vlh_total

    def _populate_vehicle_loss_hour(self, vehicle_loss_hours: gpd.GeoDataFrame, row_hazard_range: str,
                                    vlh_row: pd.Series,
                                    performance_change: float, hazard_col_name: str):

        vlh_total = 0
        if isinstance(vlh_row['link_type'], list):
            max_disruption = 0
            for row_link_type in vlh_row['link_type']:
                link_type_hazard_range = (f"{row_link_type}_{row_hazard_range}")
                row_relevant_curve = self.resilience_curve[
                    self.resilience_curve["link_type_hazard_intensity"] == link_type_hazard_range
                    ]
                disruption = ((row_relevant_curve['duration_steps'].apply(pd.Series) *
                               (row_relevant_curve['functionality_loss_ratio']).apply(pd.Series) / 100).sum(
                    axis=1)).squeeze()
                if disruption > max_disruption:
                    relevant_curve = row_relevant_curve
        else:
            row_link_type = vlh_row['link_type']
            link_type_hazard_range = (
                f"{row_link_type}_{row_hazard_range}"
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
            ].loc[[vlh_row[self.link_id]]]

            vot_trip_type = float(self.vot_intensity_per_trip_collection[
                                      f"vot_{trip_type}"
                                  ])

            vlh_trip_type_event_series = sum(
                intensity_trip_type * duration * loss_ratio * performance_change * vot_trip_type
                for duration, loss_ratio in zip(
                    duration_steps, functionality_loss_ratios
                )
            )
            vlh_trip_type_event = vlh_trip_type_event_series.squeeze()
            vehicle_loss_hours.loc[[vlh_row.name], f"vlh_{trip_type}_{hazard_col_name}"] = vlh_trip_type_event
            vlh_total += vlh_trip_type_event
        vehicle_loss_hours.loc[[vlh_row.name], f"vlh_{hazard_col_name}_total"] = vlh_total

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

    def execute(self) -> gpd.GeoDataFrame:
        criticality_analysis = SingleLinkRedundancy(self.analysis_input).execute()

        criticality_analysis.drop_duplicates(subset=self.analysis_config.config_data.network.file_id, inplace=True)

        self._get_disrupted_criticality_analysis_results(criticality_analysis=criticality_analysis)

        self.intensities_simplified_graph = self._get_intensities_simplified_graph()

        self.vot_intensity_per_trip_collection = self._get_vot_intensity_per_trip_purpose()

        self.result = self.calculate_vehicle_loss_hours()

        return self.result
