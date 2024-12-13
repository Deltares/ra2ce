import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame
from networkx import MultiDiGraph, MultiGraph

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDamages,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result import AnalysisResult
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.analysis.damages.damage_calculation import (
    DamageNetworkEvents,
    DamageNetworkReturnPeriods,
)
from ra2ce.analysis.damages.damage_functions.manual_damage_functions import (
    ManualDamageFunctions,
)
from ra2ce.analysis.damages.damage_functions.manual_damage_functions_reader import (
    ManualDamageFunctionsReader,
)
from ra2ce.analysis.damages.damages_result_wrapper import DamagesResultWrapper
from ra2ce.network.graph_files.network_file import NetworkFile


class Damages(AnalysisBase, AnalysisDamagesProtocol):
    analysis: AnalysisSectionDamages
    graph_file: NetworkFile
    graph_file_hazard: NetworkFile
    input_path: Path
    output_path: Path
    reference_base_graph_hazard: MultiGraph
    manual_damage_functions: ManualDamageFunctions = None

    def __init__(
        self, analysis_input: AnalysisInputWrapper, base_graph_hazard: MultiGraph
    ) -> None:
        self.analysis = analysis_input.analysis
        self.graph_file = None
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.output_path = analysis_input.output_path
        self.reference_base_graph_hazard = base_graph_hazard
        if self.analysis.damage_curve == DamageCurveEnum.MAN:
            self.manual_damage_functions = ManualDamageFunctionsReader().read(
                self.input_path.joinpath("damage_functions")
            )

    def execute(self) -> AnalysisResultWrapper:
        def _rename_road_gdf_to_conventions(road_gdf_columns: list[str]) -> list[str]:
            """
            Rename the columns in the road_gdf to the conventions of the ra2ce documentation

            'eg' RP100_fr -> F_RP100_me
                        -> F_EV1_mi

            """
            cs = road_gdf_columns
            ### Handle return period columns
            new_cols = []
            for c in cs:
                if c.startswith("RP") or c.startswith("EV"):
                    new_cols.append(f"{hazard_prefix}_" + c)
                else:
                    new_cols.append(c)

            ### Todo add handling of events if this gives a problem
            return new_cols

        hazard_prefix = "F"
        # Open the network with hazard data
        road_gdf = self.graph_file_hazard.get_graph()
        road_gdf.columns = _rename_road_gdf_to_conventions(road_gdf.columns)

        # Find the hazard columns; these may be events or return periods
        val_cols = [
            col for col in road_gdf.columns if f"{hazard_prefix}" in col.split("_")
        ]

        # Read the desired damage function
        damage_function = self.analysis.damage_curve

        # Choose between event or return period based analysis
        if self.analysis.event_type == EventTypeEnum.EVENT:
            event_gdf = DamageNetworkEvents(
                road_gdf, val_cols, self.analysis.representative_damage_percentage
            )
            event_gdf.main(
                damage_function=damage_function,
                manual_damage_functions=self.manual_damage_functions,
            )

            return self.generate_result_wrapper(event_gdf.gdf)

        elif self.analysis.event_type == EventTypeEnum.RETURN_PERIOD:
            return_period_gdf = DamageNetworkReturnPeriods(
                road_gdf, val_cols, self.analysis.representative_damage_percentage
            )
            return_period_gdf.main(
                damage_function=damage_function,
                manual_damage_functions=self.manual_damage_functions,
            )

            if (
                self.analysis.risk_calculation_mode != RiskCalculationModeEnum.INVALID
            ):  # Check if risk_calculation is demanded
                if self.analysis.risk_calculation_mode != RiskCalculationModeEnum.NONE:
                    return_period_gdf.control_risk_calculation(
                        self.analysis.damage_curve,
                        mode=self.analysis.risk_calculation_mode,
                        year=self.analysis.risk_calculation_year,
                    )

            else:
                logging.info(
                    """No parameters for risk calculation are specified. 
                             Add key [risk_calculation_mode] to analyses.ini."""
                )

            return self.generate_result_wrapper(return_period_gdf.gdf)

        raise ValueError(
            "The hazard calculation does not know what to do if the analysis specifies {}".format(
                self.analysis.event_type
            )
        )

    def generate_result_wrapper(
        self, *analyses_results: GeoDataFrame
    ) -> AnalysisResultWrapper:
        """
        Overloading of the parent `generate_result_wrapper` to convert the
        analysis_result which is segment base into a link base and return
        both.

        Args:
            analyses_results (list[GeoDataFrame]): Original segment based result.

        Returns:
            AnalysisResultWrapper: Result wrapper containing both link and segment based graphs.
        """
        _result_segment_based = analyses_results[0]
        _result_link_based = self._get_result_link_based(
            base_graph_hazard=self.reference_base_graph_hazard,
            result_segment_based=_result_segment_based,
        )

        def get_analysis_result(gdf_result: GeoDataFrame, name: str) -> AnalysisResult:
            _ar = AnalysisResult(
                analysis_result=gdf_result,
                analysis_config=self.analysis,
                output_path=self.output_path,
            )
            _ar.analysis_name = name
            return _ar

        return DamagesResultWrapper(
            segment_based_result=get_analysis_result(
                _result_segment_based, self.analysis.name + "_segmented"
            ),
            link_based_result=get_analysis_result(
                _result_link_based, self.analysis.name + "_link_based"
            ),
        )

    def _update_link_based_values(
        self,
        damages_link_based_graph: MultiDiGraph | MultiGraph,
        result_segment_based: pd.DataFrame,
        segment_id_column: str,
        result_column: str,
        segment_values_list: str,
    ) -> MultiDiGraph | MultiGraph:
        """
        Derive the values in the provided graph (link_based) based on the results of the segment-based graph.

        Parameters:
        - damages_link_based_graph (MultiDiGraph | MultiGraph): The graph with link-based damage data.
        - result_segment_based (pd.DataFrame): DataFrame containing segment-based damage data.
        - segment_id_column (str): The column name in both the graph data and DataFrame representing segment IDs.
        - result_column (str): The column name in the graph data and DataFrame representing the damage result.
        - segment_values_list (str): The column name in the graph data to store the segment damage values.

        Returns:
        - damages_link_based_graph (MultiDiGraph | MultiGraph)
        """
        for u, v, key, data in damages_link_based_graph.edges(keys=True, data=True):
            damages_link_based_graph[u][v][key][segment_values_list] = []
            damages_link_based_graph[u][v][key][result_column] = 0

        # Lookup segment_id_list for each edge
        for u, v, key, data in damages_link_based_graph.edges(keys=True, data=True):
            link_value = data[result_column]
            segment_id_list = (
                data[segment_id_column]
                if isinstance(data[segment_id_column], list)
                else [data[segment_id_column]]
            )

            # Read value for each segment_id & append to segment_values_list and calculate link_value
            for segment_id in segment_id_list:
                segment_value = result_segment_based.loc[
                    result_segment_based[segment_id_column] == segment_id,
                    result_column,
                ].squeeze()

                data[segment_values_list].append(round(segment_value, 2))

                if np.isnan(segment_value):
                    segment_value = 0

                link_value += round(segment_value, 2)

            data[result_column] = round(link_value, 2)
        return damages_link_based_graph

    def _get_result_link_based(
        self,
        base_graph_hazard: MultiGraph,
        result_segment_based: GeoDataFrame,
    ) -> GeoDataFrame:
        # Step 00: define parameters
        damage_curve = self.analysis.damage_curve
        segment_id_column = "rfid_c"

        # Find the hazard columns; these may be events or return periods
        event_cols = [
            col
            for col in result_segment_based.columns
            if (col[0].isupper() and col[1] == "_")
        ]
        events = set([x.split("_")[1] for x in event_cols])  # set of unique events

        # Step 0: create a deep copy of the base_graph_hazard to compose further as the final outcome of this process
        damages_link_based_graph = base_graph_hazard.copy()

        # Step 1: Create a new attribute damage_segments_list for each edge
        for event in events:
            if damage_curve == self.analysis.damage_curve.HZ:
                damage_result_columns = [
                    f"dam_{event}_{damage_curve}"
                ]  # there is one damage column
            elif damage_curve == self.analysis.damage_curve.OSD:
                pattern = rf"dam_.*_{event}_representative"
                damage_result_columns = [
                    col
                    for col in result_segment_based.columns
                    if re.match(pattern, col)
                ]
                # there are multiple damage columns
            elif damage_curve == self.analysis.damage_curve.MAN:
                pattern = rf"dam_{event}_.*"
                damage_result_columns = [
                    col
                    for col in result_segment_based.columns
                    if re.match(pattern, col)
                ]  # there are multiple damage columns
            else:
                raise ValueError(f"damage curve {damage_curve} is invalid")

            for damage_result_column in damage_result_columns:
                # Step 2: Get damage of each link.
                # Read damage for each segment_id & append to damage_segments_list and calculate link_damage
                damages_link_based_graph = self._update_link_based_values(
                    damages_link_based_graph=damages_link_based_graph,
                    result_segment_based=result_segment_based,
                    segment_id_column=segment_id_column,
                    result_column=damage_result_column,
                    segment_values_list=f"{damage_result_column}_segments",
                )

        # Step 3: get risk of each link.
        # Read risk for each segment_id & append to risk_segments_list and calculate link_risk
        if self.analysis.event_type == EventTypeEnum.RETURN_PERIOD:
            pattern = r"(risk.*)"
            risk_result_columns = [
                col for col in result_segment_based.columns if re.match(pattern, col)
            ]
            for risk_result_column in risk_result_columns:
                damages_link_based_graph = self._update_link_based_values(
                    damages_link_based_graph=damages_link_based_graph,
                    result_segment_based=result_segment_based,
                    segment_id_column=segment_id_column,
                    result_column=risk_result_column,
                    segment_values_list=f"{risk_result_column}_segments",
                )

        # Step 4: Convert the edge attributes to a GeoDataFrame
        edge_attributes = []
        for u, v, key, data in damages_link_based_graph.edges(keys=True, data=True):
            edge_attributes.append({**{"u": u, "v": v, "key": key}, **data})
        damages_link_based_gdf = GeoDataFrame(edge_attributes)
        return damages_link_based_gdf
