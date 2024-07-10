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
import re
import time

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from networkx import MultiDiGraph

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.analysis_result_wrapper_exporter import (
    AnalysisResultWrapperExporter,
)
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class DamagesAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Damages Analysis Runner"

    @staticmethod
    def _update_link_based_values(
        damages_link_based_graph: nx.MultiDiGraph | nx.MultiGraph,
        result_segment_based: pd.DataFrame,
        segment_id_column: str,
        result_column: str,
        segment_values_list: str,
    ) -> nx.MultiDiGraph | nx.MultiGraph:
        """
        Derive the values in the provided graph (link_based) based on the results of the segment-based graph.

        Parameters:
        - damages_link_based_graph (nx.MultiDiGraph | nx.MultiGraph): The graph with link-based damage data.
        - result_segment_based (pd.DataFrame): DataFrame containing segment-based damage data.
        - segment_id_column (str): The column name in both the graph data and DataFrame representing segment IDs.
        - result_column (str): The column name in the graph data and DataFrame representing the damage result.
        - segment_values_list (str): The column name in the graph data to store the segment damage values.

        Returns:
        - damages_link_based_graph (nx.MultiDiGraph | nx.MultiGraph)
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

    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        if (
            not ra2ce_input.analysis_config
            or not ra2ce_input.analysis_config.config_data.damages_list
        ):
            return False
        if not ra2ce_input.network_config:
            return False
        _network_config = ra2ce_input.network_config.config_data
        if not _network_config.hazard or not _network_config.hazard.hazard_map:
            logging.error(
                "Please define a hazard map in your network.ini file. Unable to calculate damages."
            )
            return False
        return True

    @staticmethod
    def _get_result_link_based(
        analysis: AnalysisDamagesProtocol,
        analysis_config: AnalysisConfigWrapper,
        result_segment_based: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        # Step 00: define parameters
        base_graph_hazard_graph = analysis_config.graph_files.base_graph_hazard.graph
        damage_curve = analysis.analysis.damage_curve
        segment_id_column = "rfid_c"

        # Find the hazard columns; these may be events or return periods
        event_cols = [
            col
            for col in result_segment_based.columns
            if (col[0].isupper() and col[1] == "_")
        ]
        events = set([x.split("_")[1] for x in event_cols])  # set of unique events

        # Step 0: create a deep copy of the base_graph_hazard to compose further as the final outcome of this process
        damages_link_based_graph = base_graph_hazard_graph.copy()

        # Step 1: Create a new attribute damage_segments_list for each edge
        for event in events:
            if damage_curve == analysis.analysis.damage_curve.HZ:
                damage_result_columns = [
                    f"dam_{event}_{damage_curve}"
                ]  # there is one damage column
            elif damage_curve == analysis.analysis.damage_curve.OSD:
                pattern = rf"dam_.*_{event}_representative"
                damage_result_columns = [
                    col
                    for col in result_segment_based.columns
                    if re.match(pattern, col)
                ]
                # there are multiple damage columns
            elif damage_curve == analysis.analysis.damage_curve.MAN:
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
                damages_link_based_graph = (
                    DamagesAnalysisRunner._update_link_based_values(
                        damages_link_based_graph=damages_link_based_graph,
                        result_segment_based=result_segment_based,
                        segment_id_column=segment_id_column,
                        result_column=damage_result_column,
                        segment_values_list=f"{damage_result_column}_segments",
                    )
                )

        # Step 3: get risk of each link.
        # Read risk for each segment_id & append to risk_segments_list and calculate link_risk
        if analysis.analysis.event_type == EventTypeEnum.RETURN_PERIOD:
            pattern = r"(risk.*)"
            risk_result_columns = [
                col for col in result_segment_based.columns if re.match(pattern, col)
            ]
        for risk_result_column in risk_result_columns:
            damages_link_based_graph = DamagesAnalysisRunner._update_link_based_values(
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
        damages_link_based_gdf = gpd.GeoDataFrame(edge_attributes)
        return damages_link_based_gdf

    def run(
        self, analysis_config: AnalysisConfigWrapper
    ) -> list[AnalysisResultWrapper]:
        _analysis_collection = AnalysisCollection.from_config(analysis_config)
        _results = []
        for analysis in _analysis_collection.damages_analyses:
            logging.info(
                "----------------------------- Started analyzing '%s'  -----------------------------",
                analysis.analysis.name,
            )
            starttime = time.time()

            _result_segmented = analysis.execute()
            _result_link_based = self._get_result_link_based(
                analysis=analysis,
                analysis_config=analysis_config,
                result_segment_based=_result_segmented,
            )
            analysis_name = analysis.analysis.name
            for _result, suffix in zip(
                [_result_segmented, _result_link_based], ["segmented", "link_based"]
            ):
                _result_wrapper = AnalysisResultWrapper(
                    analysis_result=_result, analysis=analysis
                )
                _result_wrapper.analysis.analysis.name = analysis_name + "_" + suffix
                _results.append(_result_wrapper)

                AnalysisResultWrapperExporter().export_result(_result_wrapper)

            endtime = time.time()
            logging.info(
                "----------------------------- Analysis '%s' finished. "
                "Time: %ss  -----------------------------",
                analysis.analysis.name,
                str(round(endtime - starttime, 2)),
            )
        return _results
