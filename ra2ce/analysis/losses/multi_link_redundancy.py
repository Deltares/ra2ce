import copy
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx
import pandas as pd

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_factory import (
    WeighingAnalysisFactory,
)
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames


class MultiLinkRedundancy(AnalysisBase, AnalysisLossesProtocol):
    analysis: AnalysisSectionLosses
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

    def _update_time(
        self, df_calculated: pd.DataFrame, gdf_graph: gpd.GeoDataFrame
    ) -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
        """
        updates the time column with the calculated dataframe and updates the rest of the gdf_graph if time is None.
        """
        if WeighingEnum.TIME.config_value not in df_calculated.columns:
            return df_calculated, gdf_graph

        if (
            WeighingEnum.TIME.config_value in gdf_graph.columns
            and WeighingEnum.TIME.config_value in df_calculated.columns
        ):
            df_calculated = df_calculated.drop(columns=[WeighingEnum.TIME.config_value])
            return df_calculated, gdf_graph

        gdf_graph[WeighingEnum.TIME.config_value] = df_calculated[
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
        return df_calculated, gdf_graph

    def execute(self) -> AnalysisResultWrapper:
        """Calculates the multi-link redundancy of a NetworkX graph.

        The function removes all links of a variable that have a minimum value
        of min_threshold. For each link it calculates the alternative path, if
        any available. This function only removes one group at the time and saves the data from removing that group.

        Returns:
            AnalysisResultWrapper: The results of the analysis aggregated into a table.
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
                u, v, _, _weighing_analyser.edge_data = edges
                _current_value = _weighing_analyser.get_current_value()

                _alt_value, _alt_nodes, _connected, _diff = np.nan, np.nan, 0, np.nan
                if nx.has_path(_graph, u, v):
                    [_alt_value, _alt_nodes] = nx.single_source_dijkstra(
                        _graph,
                        u,
                        v,
                        weight=self.analysis.weighing.config_value,
                    )
                    _connected = 1

                    _diff = round(_alt_value - _current_value, 3)

                data = {
                    "u": u,
                    "v": v,
                    self.analysis.weighing.config_value: _current_value,
                    f"alt_{self.analysis.weighing.config_value}": _alt_value,
                    "alt_nodes": [_alt_nodes],
                    f"diff_{self.analysis.weighing.config_value}": _diff,
                    "connected": _connected,
                }

                if "rfid" in gdf:
                    data["rfid"] = [str(_weighing_analyser.edge_data["rfid"])]

                df_calculated = pd.concat(
                    [df_calculated, pd.DataFrame(data)], ignore_index=True
                )

            df_calculated[f"alt_{self.analysis.weighing.config_value}"] = pd.to_numeric(
                df_calculated[f"alt_{self.analysis.weighing.config_value}"],
                errors="coerce",
            )

            df_calculated, gdf = self._update_time(df_calculated, gdf)

            # Merge the dataframes
            if "rfid" in gdf:
                gdf = gdf.merge(df_calculated, how="left", on=["u", "v", "rfid"])
            else:
                gdf = gdf.merge(df_calculated, how="left", on=["u", "v"])

            gdf["hazard"] = hazard_name

            results.append(gdf)

        return self.generate_result_wrapper(pd.concat(results, ignore_index=True))
