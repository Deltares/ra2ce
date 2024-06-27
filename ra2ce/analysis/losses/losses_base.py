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
import math
from abc import ABC, abstractmethod
from ast import literal_eval
from collections import defaultdict
from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.resilience_curve.resilience_curve_reader import (
    ResilienceCurveReader,
)
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


def _load_df_from_csv(
    csv_path: Path,
    columns_to_interpret: list[str],
    index: Optional[str | None],
    sep: str = ",",
) -> pd.DataFrame:
    if csv_path is None or not csv_path.exists():
        logging.warning("No `csv` file found at {}.".format(csv_path))
        return pd.DataFrame()

    _csv_dataframe = pd.read_csv(csv_path, sep=sep, on_bad_lines="skip")
    if "geometry" in _csv_dataframe.columns:
        raise Exception(f"The csv file in {csv_path} should not have a geometry column")

    if any(columns_to_interpret):
        _csv_dataframe[columns_to_interpret] = _csv_dataframe[
            columns_to_interpret
        ].applymap(literal_eval)
    if index:
        _csv_dataframe.set_index(index, inplace=True)
    return _csv_dataframe


class LossesBase(AnalysisLossesProtocol, ABC):
    """
    This class is the base class for the Losses analyses, containing the common methods and attributes.
    Based on the analysis type a different criticality analysis is executed.
    """

    analysis: AnalysisSectionLosses
    graph_file_hazard: GraphFile
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames

    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
        analysis_config: AnalysisConfigWrapper,
    ) -> None:
        self.analysis_input = analysis_input
        self.analysis_config = analysis_config
        self.analysis = analysis_input.analysis
        self.graph_file_hazard = analysis_input.graph_file_hazard

        self.link_id = analysis_config.config_data.network.file_id
        self.link_type_column = analysis_config.config_data.network.link_type_column
        self.trip_purposes = self.analysis.trip_purposes

        self.performance_metric = f"diff_{self.analysis.weighing}"

        self.part_of_day: PartOfDayEnum = self.analysis.part_of_day
        self.analysis_type = self.analysis.analysis
        self.duration_event: float = self.analysis.duration_event
        self.hours_per_day: float = self.analysis.hours_per_day
        self.production_loss_per_capita_per_hour = (
            self.analysis.production_loss_per_capita_per_hour
        )
        self._check_validity_analysis_files()
        self.intensities = _load_df_from_csv(
            Path(self.analysis.traffic_intensities_file), [], self.link_id
        )  # per day
        self.resilience_curve = ResilienceCurveReader().read(
            self.analysis.resilience_curve_file
        )
        self.values_of_time = _load_df_from_csv(
            Path(self.analysis.values_of_time_file), [], None, sep=";"
        )
        self._check_validity_df()

        self.input_path = analysis_input.input_path
        self.static_path = analysis_input.static_path
        self.output_path = analysis_input.output_path
        self.hazard_names = analysis_input.hazard_names

        self.result = gpd.GeoDataFrame()

    def _check_validity_analysis_files(self):
        if (
            self.analysis.traffic_intensities_file is None
            or self.analysis.resilience_curve_file is None
            or self.analysis.values_of_time_file is None
        ):
            raise ValueError(
                f"traffic_intensities_file, resilience_curve_file, and values_of_time_file should be given"
            )

    def _check_validity_df(self):
        """
        Check spelling of the required input csv files. If user writes wrong spelling, it will raise an error
        when initializing the class.
        """
        _required_values_of_time_keys = ["trip_types", "value_of_time", "occupants"]
        if not all(
            key in self.values_of_time.columns for key in _required_values_of_time_keys
        ):
            raise ValueError(
                f"Missing required columns in values_of_time: {_required_values_of_time_keys}"
            )

        if (
            self.link_id not in self.intensities.columns
            and self.link_id not in self.intensities.index.name
        ):
            raise ValueError(
                f"""traffic_intensities_file and input graph do not have the same link_id.
        {self.link_id} is passed for feature ids of the graph"""
            )

    def _get_vot_intensity_per_trip_purpose(self) -> dict[str, pd.DataFrame]:
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
                self.values_of_time["trip_types"] == trip_purpose.config_value,
                "value_of_time",
            ].item()
            _vot_dict[occupancy_var_name] = self.values_of_time.loc[
                self.values_of_time["trip_types"] == trip_purpose.config_value,
                "occupants",
            ].item()
            # read and set the intensities
            _vot_dict[partofday_trip_purpose_intensity_name] = (
                self.intensities_simplified_graph[partofday_trip_purpose_name]
                / self.hours_per_day
            )
        return dict(_vot_dict)

    def _get_disrupted_criticality_analysis_results(
        self, criticality_analysis: gpd.GeoDataFrame
    ):
        criticality_analysis.reset_index(inplace=True)

        if "key" in criticality_analysis.columns:
            criticality_analysis = criticality_analysis.drop_duplicates(
                ["u", "v", "key"]
            )
        else:
            criticality_analysis = criticality_analysis.drop_duplicates(["u", "v"])

        # filter out all links not affected by the hazard
        if self.analysis.aggregate_wl == AggregateWlEnum.NONE:
            self.criticality_analysis = criticality_analysis[
                criticality_analysis["EV1_ma"] > self.analysis.threshold
            ]
        elif self.analysis.aggregate_wl == AggregateWlEnum.MAX:
            self.criticality_analysis = criticality_analysis[
                criticality_analysis["EV1_max"] > self.analysis.threshold
            ]
        elif self.analysis.aggregate_wl == AggregateWlEnum.MEAN:
            self.criticality_analysis = criticality_analysis[
                criticality_analysis["EV1_mean"] > self.analysis.threshold
            ]
        elif self.analysis.aggregate_wl == AggregateWlEnum.MIN:
            self.criticality_analysis = criticality_analysis[
                criticality_analysis["EV1_min"] > self.analysis.threshold
            ]

        self.criticality_analysis_non_disrupted = criticality_analysis[
            ~criticality_analysis.index.isin(self.criticality_analysis.index)
        ]
        # link_id from list to tuple
        if len(self.criticality_analysis_non_disrupted) > 0:
            self.criticality_analysis_non_disrupted[
                self.link_id
            ] = self.criticality_analysis_non_disrupted[self.link_id].apply(
                lambda x: tuple(x) if isinstance(x, list) else x
            )
        self.criticality_analysis[self.link_id] = self.criticality_analysis[
            self.link_id
        ].apply(lambda x: tuple(x) if isinstance(x, list) else x)

        self.criticality_analysis.set_index(self.link_id, inplace=True)
        self.criticality_analysis_non_disrupted = (
            self.criticality_analysis_non_disrupted.reset_index()
        )

    def _get_intensities_simplified_graph(self) -> pd.DataFrame:
        _intensities_simplified_graph_list = []

        for index in self.criticality_analysis.index.values:
            if isinstance(index, tuple):
                filtered_intensities = self.intensities[
                    self.intensities.index.isin(index)
                ]

                # Create a new DataFrame with the index set to tuple_of_indices and the maximum values as the values
                max_intensities = filtered_intensities.max().to_frame().T
                max_intensities.index = [index]

                row_data = max_intensities.squeeze()
            else:
                row_data = self.intensities.loc[int(index)]

            _intensities_simplified_graph_list.append(row_data)
        _intensities_simplified_graph = pd.DataFrame(
            _intensities_simplified_graph_list,
            index=self.criticality_analysis.index.values,
        )
        # no duplicate exists in the intensities and _intensities_simplified_graph. each link has its own intensity and
        # ID in these files
        _intensities_simplified_graph = _intensities_simplified_graph[
            ~_intensities_simplified_graph.index.duplicated(keep="first")
        ]
        return _intensities_simplified_graph

    def calculate_vehicle_loss_hours(self) -> gpd.GeoDataFrame:
        """
        This function opens an existing table with traffic data and value of time to calculate losses based on
        detouring values. It also includes a traffic jam estimation.
        """

        def _check_validity_criticality_analysis():
            if self.link_type_column not in self.criticality_analysis.columns:
                raise Exception(
                    f"""criticality_analysis results does not have the passed link_type_column.
            {self.link_type_column} is passed as link_type_column"""
                )

        def _get_range(height: float) -> tuple[float, float]:
            for range_tuple in _hazard_intensity_ranges:
                x, y = range_tuple
                if x <= height <= y:
                    return (x, y)
            raise ValueError(f"No matching range found for height {height}")

        def _create_result(
            vlh: gpd.GeoDataFrame, connectivity_attribute: str
        ) -> gpd.GeoDataFrame:
            """

            Args: vlh: calculated vehicle_loss_hours GeoDataFrame. For single_link_losses it only includes the
            disrupted links. For Multi_link_losses it includes all links. This is because of the difference between
            the underlying single_link_redundancy and multi_link_redundancy analysis results.

            Returns: results of the Losses analysis. For the single_link_losses it adds non_disrupted links to vlh. For
            Multi_link_losses this is not necessary because of the underlying multi_link_redundancy analysis.

            """
            columns_without_index = [
                col
                for col in self.criticality_analysis_non_disrupted.columns
                if col not in ["level_0"]
            ]
            # Get the vlh_columns from vehicle_loss_hours that vlh calculations are filled in.
            vlh_columns = list(
                set(vlh.columns)
                - set(
                    self.criticality_analysis_non_disrupted[
                        columns_without_index
                    ].columns
                )
            )
            vlh[vlh_columns] = vlh[vlh_columns].fillna(0)

            result = pd.concat(
                [
                    vlh,
                    self.criticality_analysis_non_disrupted[columns_without_index],
                ]
            )
            result = result.reset_index()

            # Fill 0 for the vlh_columns of vlh and self.criticality_analysis_non_disrupted
            result.loc[result.index.difference(vlh.index), vlh_columns] = result.loc[
                result.index.difference(vlh.index), vlh_columns
            ].fillna(0)
            for col in ["index", "level_0"]:
                if col in result.columns:
                    result = result.drop(col, axis=1)

            return result

        _check_validity_criticality_analysis()

        _hazard_intensity_ranges = self.resilience_curve.ranges
        events = self.criticality_analysis.filter(regex=r"^EV(?!1_fr)")
        # Read the performance_change stating the functionality drop
        if "key" in self.criticality_analysis.columns:
            performance_change = self.criticality_analysis[
                [f"{self.performance_metric}", "u", "v", "key"]
            ]
            vehicle_loss_hours_df = pd.DataFrame(
                {
                    f"{self.link_id}": self.criticality_analysis.index.values,
                    "u": self.criticality_analysis["u"],
                    "v": self.criticality_analysis["v"],
                    "key": self.criticality_analysis["key"],
                }
            )
        else:
            performance_change = self.criticality_analysis[
                [f"{self.performance_metric}", "u", "v"]
            ]
            vehicle_loss_hours_df = pd.DataFrame(
                {
                    f"{self.link_id}": self.criticality_analysis.index.values,
                    "u": self.criticality_analysis["u"],
                    "v": self.criticality_analysis["v"],
                }
            )

        # shape vehicle_loss_hours
        # Check if the index name exists in the columns
        if vehicle_loss_hours_df.index.name in vehicle_loss_hours_df.columns:
            vehicle_loss_hours_df.reset_index(drop=True, inplace=True)
        else:
            vehicle_loss_hours_df.reset_index(inplace=True)

        # find the link_type and the hazard intensity
        connectivity_attribute = None
        if any(
            col in self.criticality_analysis.columns for col in ["detour", "connected"]
        ):
            connectivity_attribute = (
                "detour"
                if "detour" in self.criticality_analysis.columns
                else "connected"
            )
        vlh_additional_columns = self.criticality_analysis.columns.difference(
            vehicle_loss_hours_df.columns
        ).tolist()
        vehicle_loss_hours_df = pd.merge(
            vehicle_loss_hours_df,
            self.criticality_analysis[vlh_additional_columns],
            left_on=self.link_id,
            right_index=True,
        )
        vehicle_loss_hours = gpd.GeoDataFrame(
            vehicle_loss_hours_df,
            geometry="geometry",
            crs=self.criticality_analysis.crs,
        )
        for event in events.columns.tolist():
            for _, vlh_row in vehicle_loss_hours.iterrows():
                row_hazard_range = _get_range(vlh_row[event])
                row_connectivity = vlh_row[connectivity_attribute]
                row_performance_changes = performance_change.loc[
                    [vlh_row[self.link_id]]
                ]
                if "key" in vlh_row.index:
                    key = vlh_row["key"]
                else:
                    key = 0
                (u, v, k) = (
                    vlh_row["u"],
                    vlh_row["v"],
                    key,
                )
                # allow link_id not to be unique in the graph (results reliability is up to the user)
                # this can happen for instance when a directed graph should be made from an input network
                for performance_row in row_performance_changes.iterrows():
                    row_performance_change = performance_row[-1][
                        f"{self.performance_metric}"
                    ]
                    if "key" in performance_row[-1].index:
                        performance_key = performance_row[-1]["key"]
                    else:
                        performance_key = 0
                    row_u_v_k = (
                        performance_row[-1]["u"],
                        performance_row[-1]["v"],
                        performance_key,
                    )
                    if (
                        math.isnan(row_performance_change) and row_connectivity == 0
                    ) or row_performance_change == 0:
                        self._calculate_production_loss_per_capita(
                            vehicle_loss_hours, vlh_row, event
                        )
                    elif not (
                        math.isnan(row_performance_change)
                        and math.isnan(row_connectivity)
                    ) and ((u, v, k) == row_u_v_k):
                        self._populate_vehicle_loss_hour(
                            vehicle_loss_hours,
                            row_hazard_range,
                            vlh_row,
                            row_performance_change,
                            event,
                        )

        vehicle_loss_hours_result = _create_result(
            vehicle_loss_hours, connectivity_attribute
        )
        return vehicle_loss_hours_result

    def _calculate_production_loss_per_capita(
        self,
        vehicle_loss_hours: gpd.GeoDataFrame,
        vlh_row: pd.Series,
        hazard_col_name: str,
    ):
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
            occupancy_trip_type = float(
                self.vot_intensity_per_trip_collection[f"occupants_{trip_type}"]
            )
            # TODO: improve formula based on road_type, water_heigth resilience_curve.csv (duration*loss_ratio) instead of duration_event
            # Compare with other function
            vlh_trip_type_event_series = (
                self.duration_event
                * intensity_trip_type
                * occupancy_trip_type
                * self.production_loss_per_capita_per_hour
            )
            vlh_trip_type_event = vlh_trip_type_event_series.squeeze()
            vehicle_loss_hours.loc[
                [vlh_row.name], f"vlh_{trip_type}_{hazard_col_name}"
            ] = vlh_trip_type_event
            vlh_total += vlh_trip_type_event
        vehicle_loss_hours.loc[
            [vlh_row.name], f"vlh_{hazard_col_name}_total"
        ] = vlh_total

    def _populate_vehicle_loss_hour(
        self,
        vehicle_loss_hours: gpd.GeoDataFrame,
        row_hazard_range: tuple[float, float],
        vlh_row: pd.Series,
        performance_change: float,
        hazard_col_name: str,
    ):

        # Check if the resilience curve is present for the link type and hazard intensity
        vlh_total = 0
        _relevant_link_type = None
        if isinstance(vlh_row[self.link_type_column], list):
            # Find the link type with the highest disruption for the given hazard intensity
            _max_disruption = 0
            for _row_link_type in vlh_row[self.link_type_column]:
                _link_type = RoadTypeEnum.get_enum(_row_link_type)
                disruption = self.resilience_curve.get_disruption(
                    _link_type, row_hazard_range[0]
                )
                if disruption > _max_disruption:
                    _relevant_link_type = _link_type
        else:
            _link_type = RoadTypeEnum.get_enum(vlh_row[self.link_type_column])
            if self.resilience_curve.has_resilience_curve(
                _link_type,
                row_hazard_range[0],
            ):
                _relevant_link_type = _link_type

        if not _relevant_link_type:
            raise ValueError(
                f"'{_link_type}' with range {row_hazard_range} was not found in the introduced resilience_curve"
            )

        divisor = 100  # high value assuming the road is almost inaccessible
        if all(
            ratio <= 1
            for ratio in self.resilience_curve.get_functionality_loss_ratio(
                _relevant_link_type, row_hazard_range[0]
            )
        ):
            divisor = 1

        duration_steps = self.resilience_curve.get_duration_steps(
            _relevant_link_type, row_hazard_range[0]
        )
        functionality_loss_ratios = self.resilience_curve.get_functionality_loss_ratio(
            _relevant_link_type, row_hazard_range[0]
        )

        # get vlh_trip_type_event
        for trip_type in self.trip_purposes:
            intensity_trip_type = self.vot_intensity_per_trip_collection[
                f"intensity_{self.part_of_day}_{trip_type}"
            ].loc[[vlh_row[self.link_id]]]

            vot_trip_type = float(
                self.vot_intensity_per_trip_collection[f"vot_{trip_type}"]
            )

            vlh_trip_type_event_series = sum(
                (
                    intensity_trip_type
                    * duration
                    * loss_ratio
                    * performance_change
                    * vot_trip_type
                )
                / divisor
                for duration, loss_ratio in zip(
                    duration_steps, functionality_loss_ratios
                )
            )
            vlh_trip_type_event = vlh_trip_type_event_series.squeeze()
            vehicle_loss_hours.loc[
                [vlh_row.name], f"vlh_{trip_type}_{hazard_col_name}"
            ] = vlh_trip_type_event
            vlh_total += vlh_trip_type_event
        vehicle_loss_hours.loc[
            [vlh_row.name], f"vlh_{hazard_col_name}_total"
        ] = vlh_total

    @abstractmethod
    def _get_criticality_analysis(self) -> AnalysisLossesProtocol:
        pass

    def execute(self) -> gpd.GeoDataFrame:
        criticality_analysis = self._get_criticality_analysis().execute()

        self._get_disrupted_criticality_analysis_results(
            criticality_analysis=criticality_analysis
        )

        self.intensities_simplified_graph = self._get_intensities_simplified_graph()

        self.vot_intensity_per_trip_collection = (
            self._get_vot_intensity_per_trip_purpose()
        )

        self.result = self.calculate_vehicle_loss_hours()
        return self.result
