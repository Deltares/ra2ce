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
from pathlib import Path

import pandas as pd
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.resilience_curves.resilience_curves_reader import (
    ResilienceCurvesReader,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_factory import (
    RiskCalculationFactory,
)
from ra2ce.analysis.losses.time_values.time_values_reader import TimeValuesReader
from ra2ce.analysis.losses.traffic_intensities.traffic_intensities_reader import (
    TrafficIntensitiesReader,
)
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class LossesBase(AnalysisLossesProtocol, AnalysisBase, ABC):
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
        self.trip_purposes: list[TripPurposeEnum] = self.analysis.trip_purposes

        self.performance_metric = f"diff_{self.analysis.weighing}"

        self.analysis_type = self.analysis.analysis
        self.traffic_period: TrafficPeriodEnum = self.analysis.traffic_period
        self.hours_per_traffic_period: float = self.analysis.hours_per_traffic_period
        if not self.hours_per_traffic_period:
            self.hours_per_traffic_period = 24
            if self.traffic_period != TrafficPeriodEnum.DAY:
                logging.warning(
                    "No value set for `hours_per_traffic_period`. Assuming 24 hours per traffic period."
                )

        self.production_loss_per_capita_per_hour = (
            self.analysis.production_loss_per_capita_per_hour
        )

        self._check_validity_analysis_files()
        self.intensities = TrafficIntensitiesReader([self.link_id]).read(
            self.analysis.traffic_intensities_file
        )
        self.resilience_curves = ResilienceCurvesReader().read(
            self.analysis.resilience_curves_file
        )
        self.values_of_time = TimeValuesReader().read(self.analysis.values_of_time_file)

        self.input_path = analysis_input.input_path
        self.static_path = analysis_input.static_path
        self.output_path = analysis_input.output_path
        self.hazard_names = analysis_input.hazard_names

        self.criticality_analysis = GeoDataFrame()
        self.criticality_analysis_non_disrupted = GeoDataFrame()
        self.result = GeoDataFrame()

    def _check_validity_analysis_files(self):
        if (
            self.analysis.traffic_intensities_file is None
            or self.analysis.resilience_curves_file is None
            or self.analysis.values_of_time_file is None
        ):
            raise ValueError(
                "traffic_intensities_file, resilience_curves_file, and values_of_time_file should be given"
            )

    def _get_disrupted_criticality_analysis_results(
        self, criticality_analysis: GeoDataFrame
    ):
        criticality_analysis.reset_index(inplace=True)

        if "key" in criticality_analysis.columns:
            criticality_analysis = criticality_analysis.drop_duplicates(
                ["u", "v", "key"]
            )
        else:
            criticality_analysis = criticality_analysis.drop_duplicates(["u", "v"])
        #  ToDO: check hazard overlay with AggregateWlEnum.NONE or INVALID

        aggregate_wl_abbreviation = (
            self.analysis_config.config_data.aggregate_wl.get_wl_abbreviation()
        )
        hazard_aggregate_wl_columns = [
            c
            for c in criticality_analysis.columns
            if (c.startswith("RP") or c.startswith("EV"))
            and c.endswith(f"_{aggregate_wl_abbreviation}")
        ]
        self.criticality_analysis = criticality_analysis[
            (
                criticality_analysis[hazard_aggregate_wl_columns]
                > self.analysis.threshold
            ).any(axis=1)
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

    def calculate_vehicle_loss_hours(self) -> GeoDataFrame:
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
                    return x, y
            raise ValueError(f"No matching range found for height {height}")

        def _create_result(vlh: GeoDataFrame) -> GeoDataFrame:
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

        _hazard_intensity_ranges = self.resilience_curves.ranges
        events = self.criticality_analysis.filter(regex=r"^(EV|RP)(?!\d+_fr)")
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
        vehicle_loss_hours = GeoDataFrame(
            vehicle_loss_hours_df,
            geometry="geometry",
            crs=self.criticality_analysis.crs,
        )
        for event in events.columns.tolist():
            for _, vlh_row in vehicle_loss_hours.iterrows():
                if vlh_row[event] > self.analysis.threshold:
                    row_hazard_range = _get_range(vlh_row[event])
                    row_connectivity = vlh_row[connectivity_attribute]
                    row_performance_changes = performance_change.loc[
                        [vlh_row[self.link_id]]
                    ]
                    if "key" in vlh_row.index:
                        key = vlh_row["key"]
                    else:
                        key = 0
                    (u, v) = (vlh_row["u"], vlh_row["v"])
                    # allow link_id not to be unique in the graph (results reliability is up to the user)
                    # this can happen for instance when a directed graph should be made from an input network
                    for performance_row in row_performance_changes.iterrows():
                        row_performance_change = performance_row[-1][
                            f"{self.performance_metric}"
                        ]
                        performance_key = 0
                        if "key" in performance_row[-1].index:
                            performance_key = performance_row[-1]["key"]
                        row_u_v_k = (
                            performance_row[-1]["u"],
                            performance_row[-1]["v"],
                            performance_key,
                        )
                        if (
                            math.isnan(row_performance_change) and row_connectivity == 0
                        ) or row_performance_change == 0:
                            self._calculate_production_loss_per_capita(
                                vehicle_loss_hours, row_hazard_range, vlh_row, event
                            )
                        elif not (
                            math.isnan(row_performance_change)
                            and math.isnan(row_connectivity)
                        ) and ((u, v, key) == row_u_v_k):
                            self._populate_vehicle_loss_hour(
                                vehicle_loss_hours,
                                row_hazard_range,
                                vlh_row,
                                row_performance_change,
                                event,
                            )

        vehicle_loss_hours_result = _create_result(vehicle_loss_hours)
        return vehicle_loss_hours_result

    def _get_relevant_link_type(
        self, vlh_row: pd.Series, row_hazard_range: tuple[float, float]
    ) -> RoadTypeEnum:
        # Check if the resilience curve is present for the link type and hazard intensity
        _relevant_link_type = None
        if isinstance(vlh_row[self.link_type_column], list):
            # Find the link type with the highest disruption for the given hazard intensity
            _max_disruption = 0
            for _row_link_type in vlh_row[self.link_type_column]:
                _link_type = RoadTypeEnum.get_enum(_row_link_type)
                disruption = self.resilience_curves.calculate_disruption(
                    _link_type, row_hazard_range
                )
                if disruption > _max_disruption:
                    _relevant_link_type = _link_type
        else:
            _link_type = RoadTypeEnum.get_enum(vlh_row[self.link_type_column])
            if self.resilience_curves.has_resilience_curve(
                _link_type,
                row_hazard_range,
            ):
                _relevant_link_type = _link_type

        if not _relevant_link_type:
            raise ValueError(
                f"'{_link_type}' with range {row_hazard_range} was not found in the introduced resilience_curves"
            )

        return _relevant_link_type

    def _get_divisor(
        self, relevant_link_type: RoadTypeEnum, row_hazard_range: tuple[float, float]
    ):
        if all(
            ratio <= 1
            for ratio in self.resilience_curves.get_functionality_loss_ratio(
                relevant_link_type, row_hazard_range
            )
        ):
            return 1
        return 100  # high value assuming the road is almost inaccessible

    def _calculate_production_loss_per_capita(
        self,
        vehicle_loss_hours: GeoDataFrame,
        row_hazard_range: tuple[float, float],
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

        The unit of time is hour.
        """
        vlh_total = 0
        _relevant_link_type = self._get_relevant_link_type(vlh_row, row_hazard_range)
        _divisor = self._get_divisor(_relevant_link_type, row_hazard_range)

        duration_steps = self.resilience_curves.get_duration_steps(
            _relevant_link_type, row_hazard_range
        )
        functionality_loss_ratios = self.resilience_curves.get_functionality_loss_ratio(
            _relevant_link_type, row_hazard_range
        )

        for trip_type in self.trip_purposes:
            intensity_trip_type = (
                self.intensities.calculate_intensity(
                    vlh_row[self.link_id], self.traffic_period, trip_type
                )
                / self.hours_per_traffic_period
            )

            occupancy_trip_type = self.values_of_time.get_occupants(trip_type)
            vlh_trip_type_event = sum(
                (
                    intensity_trip_type
                    * duration**2
                    * loss_ratio
                    * occupancy_trip_type
                    * self.production_loss_per_capita_per_hour
                )
                / _divisor
                for duration, loss_ratio in zip(
                    duration_steps, functionality_loss_ratios
                )
            )

            vehicle_loss_hours.loc[
                [vlh_row.name], f"vlh_{trip_type}_{hazard_col_name}"
            ] = vlh_trip_type_event
            vlh_total += vlh_trip_type_event
        vehicle_loss_hours.loc[
            [vlh_row.name], f"vlh_{hazard_col_name}_total"
        ] = vlh_total

    def _populate_vehicle_loss_hour(
        self,
        vehicle_loss_hours: GeoDataFrame,
        row_hazard_range: tuple[float, float],
        vlh_row: pd.Series,
        performance_change: float,
        hazard_col_name: str,
    ):

        vlh_total = 0
        _relevant_link_type = self._get_relevant_link_type(vlh_row, row_hazard_range)
        _divisor = self._get_divisor(_relevant_link_type, row_hazard_range)

        duration_steps = self.resilience_curves.get_duration_steps(
            _relevant_link_type, row_hazard_range
        )
        functionality_loss_ratios = self.resilience_curves.get_functionality_loss_ratio(
            _relevant_link_type, row_hazard_range
        )

        # get vlh_trip_type_event
        for trip_type in self.trip_purposes:
            intensity_trip_type = (
                self.intensities.calculate_intensity(
                    vlh_row[self.link_id], self.traffic_period, trip_type
                )
                / self.hours_per_traffic_period
            )

            vot_trip_type = self.values_of_time.get_value_of_time(trip_type)

            vlh_trip_type_event = sum(
                (
                    intensity_trip_type
                    * duration
                    * loss_ratio
                    * performance_change
                    * vot_trip_type
                )
                / _divisor
                for duration, loss_ratio in zip(
                    duration_steps, functionality_loss_ratios
                )
            )
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

    def execute(self) -> AnalysisResultWrapper:
        _criticality_analysis_result_wrapper = (
            self._get_criticality_analysis().execute()
        )

        self._get_disrupted_criticality_analysis_results(
            criticality_analysis=_criticality_analysis_result_wrapper.get_single_result()
        )

        self.result = self.calculate_vehicle_loss_hours()

        # Calculate the risk or estimated annual losses if applicable
        if (
            self.analysis.event_type == EventTypeEnum.RETURN_PERIOD
            and self.analysis.risk_calculation_mode
            not in (RiskCalculationModeEnum.INVALID, RiskCalculationModeEnum.NONE)
        ):
            risk_calculation = RiskCalculationFactory.get_risk_calculation(
                risk_calculation_mode=self.analysis.risk_calculation_mode,
                risk_calculation_year=self.analysis.risk_calculation_year,
                losses_gdf=self.result,
            )
            risk = risk_calculation.get_integration_of_df_trapezoidal()
            self.result[f"risk_vlh_total"] = risk

        return self.generate_result_wrapper(self.result)
