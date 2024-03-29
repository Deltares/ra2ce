import copy
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx
import pandas as pd
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.analysis.indirect.weighing_analysis.weighing_analysis_factory import (
    WeighingAnalysisFactory,
)
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames


class MultiLinkRedundancy(AnalysisIndirectProtocol):
    analysis: AnalysisSectionIndirect
    graph_file_hazard: GraphFile
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: HazardNames

    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
    ) -> None:
        self.analysis = analysis_input.analysis
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.static_path = analysis_input.static_path
        self.output_path = analysis_input.output_path
        self.hazard_names = analysis_input.hazard_names

    def _update_time(self, gdf_calculated: pd.DataFrame, gdf_graph: gpd.GeoDataFrame):
        """
        updates the time column with the calculated dataframe and updates the rest of the gdf_graph if time is None.
        """
        if (
            WeighingEnum.TIME.config_value not in gdf_graph.columns
            or WeighingEnum.TIME.config_value not in gdf_calculated.columns
        ):
            return gdf_graph
        gdf_graph[WeighingEnum.TIME.config_value] = gdf_calculated[
            WeighingEnum.TIME.config_value
        ]
        for i, row in gdf_graph.iterrows():
            row_avgspeed = row.get("avgspeed", None)
            row_length = row.get("length", None)
            if (
                pd.isna(row[WeighingEnum.TIME.config_value])
                and row_avgspeed
                and row_length
            ):
                gdf_graph.at[i, WeighingEnum.TIME.config_value] = (
                    row_length * 1e-3 / row_avgspeed
                )
            else:
                gdf_graph.at[i, WeighingEnum.TIME.config_value] = row.get(
                    WeighingEnum.TIME.config_value, None
                )
        return gdf_graph

    def execute(self) -> GeoDataFrame:
        """Calculates the multi-link redundancy of a NetworkX graph.

        The function removes all links of a variable that have a minimum value
        of min_threshold. For each link it calculates the alternative path, if
        any available. This function only removes one group at the time and saves the data from removing that group.

        Returns:
            aggregated_results (GeoDataFrame): The results of the analysis aggregated into a table.
        """

        def _is_not_none(value):
            return (
                value is not None
                and value is not pd.NA
                and not pd.isna(value)
                and not np.isnan(value)
            )

        results = []
        master_graph = copy.deepcopy(self.graph_file_hazard.get_graph())
        for hazard in self.hazard_names.names:
            hazard_name = self.hazard_names.get_name(hazard)

            _graph = copy.deepcopy(master_graph)
            # Create a geodataframe from the full graph
            gdf = osmnx.graph_to_gdfs(master_graph, nodes=False)
            if "rfid" in gdf:
                gdf["rfid"] = gdf["rfid"].astype(str)

            # Create the edgelist that consist of edges that should be removed
            edges_remove = []
            for e in _graph.edges.data(keys=True):
                if (hazard_name in e[-1]) and (
                    ("bridge" not in e[-1])
                    or ("bridge" in e[-1] and e[-1]["bridge"] != "yes")
                ):
                    edges_remove.append(e)
            edges_remove = [e for e in edges_remove if (e[-1][hazard_name] is not None)]
            edges_remove = [
                e
                for e in edges_remove
                if (hazard_name in e[-1])
                and (
                    _is_not_none(e[-1][hazard_name])
                    and (e[-1][hazard_name] > float(self.analysis.threshold))
                    and (
                        ("bridge" not in e[-1])
                        or ("bridge" in e[-1] and e[-1]["bridge"] != "yes")
                    )
                )
            ]

            _graph.remove_edges_from(edges_remove)

            columns = [
                "u",
                "v",
                f"alt_{self.analysis.weighing.config_value}",
                "alt_nodes",
                f"diff_{self.analysis.weighing.config_value}",
                "connected",
            ]

            if "rfid" in gdf:
                columns.insert(2, "rfid")

            df_calculated = pd.DataFrame(columns=columns)
            _weighing_analyser = WeighingAnalysisFactory.get_analysis(
                self.analysis.weighing
            )

            for edges in edges_remove:
                u, v, k, _weighing_analyser.weighing_data = edges

                if nx.has_path(_graph, u, v):
                    alt_dist = nx.dijkstra_path_length(
                        _graph, u, v, weight=WeighingEnum.LENGTH.config_value
                    )
                    alt_nodes = nx.dijkstra_path(_graph, u, v)
                    connected = 1
                    alt_value = _weighing_analyser.calculate_alternative_distance(
                        alt_dist
                    )
                else:
                    alt_value = _weighing_analyser.calculate_distance()
                    alt_nodes, connected = np.NaN, 0

                diff = round(
                    alt_value
                    - _weighing_analyser.weighing_data[
                        self.analysis.weighing.config_value
                    ],
                    3,
                )

                data = {
                    "u": [u],
                    "v": [v],
                    f"alt_{self.analysis.weighing.config_value}": [alt_value],
                    "alt_nodes": [alt_nodes],
                    f"diff_{self.analysis.weighing.config_value}": diff,
                    "connected": [connected],
                }
                _weighing_analyser.extend_graph(data)

                if "rfid" in gdf:
                    data["rfid"] = [str(_weighing_analyser.weighing_data["rfid"])]

                df_calculated = pd.concat(
                    [df_calculated, pd.DataFrame(data)], ignore_index=True
                )
            df_calculated[f"alt_{self.analysis.weighing.config_value}"] = pd.to_numeric(
                df_calculated[f"alt_{self.analysis.weighing.config_value}"],
                errors="coerce",
            )

            # Merge the dataframes
            if "rfid" in gdf:
                gdf = gdf.merge(df_calculated, how="left", on=["u", "v", "rfid"])
            else:
                gdf = gdf.merge(df_calculated, how="left", on=["u", "v"])

            gdf = self._update_time(df_calculated, gdf)

            gdf["hazard"] = hazard_name

            results.append(gdf)

        return pd.concat(results, ignore_index=True)
