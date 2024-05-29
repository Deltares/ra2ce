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
import time
import numpy as np
import geopandas as gpd
import re
import networkx as nx


from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.analysis_result_wrapper_exporter import (
    AnalysisResultWrapperExporter,
)
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class DirectAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Direct Analysis Runner"

    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        if (
            not ra2ce_input.analysis_config
            or not ra2ce_input.analysis_config.config_data.direct
        ):
            return False
        if not ra2ce_input.network_config:
            return False
        _network_config = ra2ce_input.network_config.config_data
        if not _network_config.hazard or not _network_config.hazard.hazard_map:
            logging.error(
                "Please define a hazard map in your network.ini file. Unable to calculate direct damages."
            )
            return False
        return True

    @staticmethod
    def _get_result_link_based(
        analysis: AnalysisDirectProtocol,
        analysis_config: AnalysisConfigWrapper,
        result_segment_based: gpd.GeoDataFrame,
    ) -> gpd.GeoDataFrame:
        def get_damage_result_columns(
            damage_curve: DamageCurveEnum,
            event: str,
            result_segment_based: gpd.GeoDataFrame,
        ) -> list[str]:
            if (
                damage_curve == DamageCurveEnum.HZ
            ):  # Replace with the actual enum or constant if needed
                damage_result_columns = [
                    f"dam_{event}_{damage_curve}"
                ]  # there is one damage column
            elif (
                damage_curve == DamageCurveEnum.OSD
            ):  # Replace with the actual enum or constant if needed
                pattern = rf"dam_.*_{event}_representative"
                damage_result_columns = [
                    col
                    for col in result_segment_based.columns
                    if re.match(pattern, col)
                ]
                # there are multiple damage columns
            elif (
                damage_curve == DamageCurveEnum.MAN
            ):  # Replace with the actual enum or constant if needed
                pattern = rf"dam_{event}_.*"
                damage_result_columns = [
                    col
                    for col in result_segment_based.columns
                    if re.match(pattern, col)
                ]  # there are multiple damage columns
            else:
                raise ValueError(f"damage curve {damage_curve.name} is invalid")

            return damage_result_columns

        def calculate_link_damage(
            graph: nx.MultiDiGraph,
            segment_id_column: str,
            result_segment_based: gpd.GeoDataFrame,
            damage_result_column: str,
        ) -> nx.MultiDiGraph:
            for u, v, key, data in graph.edges(keys=True, data=True):
                damage_segments_list = []
                segment_id_list = (
                    data[segment_id_column]
                    if isinstance(data[segment_id_column], list)
                    else [data[segment_id_column]]
                )

                for segment_id in segment_id_list:
                    segment_damage = result_segment_based.loc[
                        result_segment_based[segment_id_column] == segment_id,
                        damage_result_column,
                    ].squeeze()
                    if np.isnan(segment_damage):
                        segment_damage = 0.0
                    damage_segments_list.append(round(segment_damage, 2))

                data[f"{damage_result_column}_segments"] = damage_segments_list
                data[damage_result_column] = sum(damage_segments_list)

            return graph

        # Step 0: Find the hazard columns; these may be events or return periods
        base_graph_hazard_graph = analysis_config.graph_files.base_graph_hazard.graph
        damage_curve = analysis.analysis.damage_curve
        segment_id_column = "rfid_c"
        event_cols = [
            col
            for col in result_segment_based.columns
            if (col[0].isupper() and col[1] == "_")
        ]
        events = set(x.split("_")[1] for x in event_cols)  # set of unique events

        # Step 1: create a deep copy of the base_graph_hazard to compose further as the final outcome of this process
        damages_link_based_graph = base_graph_hazard_graph.copy()

        for event in events:
            # Step 2: Get the damage_result_columns representing the estimated damages for network segments
            damage_result_columns = get_damage_result_columns(
                damage_curve, event, result_segment_based
            )

            # Step 3: Lookup segment ID list and calculate damage
            for damage_result_column in damage_result_columns:
                damages_link_based_graph = calculate_link_damage(
                    damages_link_based_graph,
                    segment_id_column,
                    result_segment_based,
                    damage_result_column,
                )

        # Step 4: Convert the edge attributes to a GeoDataFrame
        edge_attributes = []
        for u, v, key, data in damages_link_based_graph.edges(keys=True, data=True):
            edge_attributes.append({**{"u": u, "v": v, "key": key}, **data})
        return gpd.GeoDataFrame(edge_attributes)

    def run(
        self, analysis_config: AnalysisConfigWrapper
    ) -> list[AnalysisResultWrapper]:
        _analysis_collection = AnalysisCollection.from_config(analysis_config)
        _results = []
        for analysis in _analysis_collection.direct_analyses:
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
