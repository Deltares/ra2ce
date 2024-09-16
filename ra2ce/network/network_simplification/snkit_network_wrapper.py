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
from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
from shapely import MultiLineString
from shapely.ops import linemerge
from snkit.network import Network

from ra2ce.network.network_simplification.nx_to_snkit_network_converter import (
    NxToSnkitNetworkConverter,
)
from ra2ce.network.network_simplification.snkit_network_merge_wrapper import merge_edges
from ra2ce.network.network_simplification.snkit_to_nx_network_converter import (
    SnkitToNxNetworkConverter,
)
from ra2ce.network.networks_utils import line_length

NxGraph = nx.Graph | nx.MultiGraph | nx.MultiDiGraph


@dataclass(kw_only=True)
class SnkitNetworkWrapper:
    """
    Wrapper created to reduce complexity of conversion and processing of a `snkit.network.Network`
    within the rest of the code.
    """

    snkit_network: Network
    node_id_column_name: str
    edge_from_id_column_name: str
    edge_to_id_column_name: str

    def __init__(
        self,
        snkit_network: Network,
        node_id_column_name: str,
        edge_from_id_column_name: str,
        edge_to_id_column_name: str,
    ) -> None:
        self.snkit_network = snkit_network
        self.node_id_column_name = node_id_column_name
        self.edge_from_id_column_name = edge_from_id_column_name
        self.edge_to_id_column_name = edge_to_id_column_name

    @classmethod
    def from_networkx(
        cls,
        networkx_graph: NxGraph,
        column_names_dict: dict[str, str],
    ) -> SnkitNetworkWrapper:
        """
        Generates a `SnkitNetworkWrapper` based on the given `NxGraph`.

        Args:
            networkx_graph (NxGraph): Graph to convert.
            column_names_dict (dict[str, str]): Column names to use.

        Returns:
            SnkitNetworkWrapper: Wrapper containing the converted `snkit.network.Network`.
        """
        _snkit_converted_network = NxToSnkitNetworkConverter(
            networkx_graph=networkx_graph, **column_names_dict
        ).convert()
        return cls(
            snkit_network=_snkit_converted_network,
            **column_names_dict,
        )

    def merge_edges(self, attributes_to_exclude: list[str]) -> None:
        def filter_excluded_attributes() -> list[str]:
            columns_set = set(self.snkit_network.edges.columns)
            return [attr for attr in attributes_to_exclude if attr in columns_set]

        cols = [col for col in self.snkit_network.edges.columns if col != "geometry"]
        _attributes_to_exclude = filter_excluded_attributes()

        if "demand_edge" not in _attributes_to_exclude:
            _aggregate_function = self._aggrfunc(
                cols, _attributes_to_exclude, with_demand=True
            )
        else:
            _aggregate_function = self._aggrfunc(
                cols, _attributes_to_exclude, with_demand=False
            )

        # Overwrite the existing network with the merged edges.
        self.snkit_network = merge_edges(
            snkit_network=self.snkit_network,
            networkx_graph=self.to_networkx(),
            aggregate_func=_aggregate_function,
            by=_attributes_to_exclude,
            id_col="id",
        )

    def process_network(self) -> None:
        _network_crs = self.snkit_network.edges.crs
        self.snkit_network.edges["length"] = self.snkit_network.edges["geometry"].apply(
            lambda x: line_length(x, _network_crs)
        )  # length in m
        self.snkit_network.edges = self.snkit_network.edges[
            self.snkit_network.edges["length"] != 0
        ]  # Remove zero-length edges

        def convert_to_line_string(geometry_to_convert) -> MultiLineString:
            if isinstance(geometry_to_convert, MultiLineString):
                return linemerge([line for line in geometry_to_convert.geoms])
            return geometry_to_convert

        self.snkit_network.edges["geometry"] = self.snkit_network.edges[
            "geometry"
        ].apply(convert_to_line_string)

    def to_networkx(self) -> NxGraph:
        """
        Converts the wrapped `snkit_network` into a corresponding `networkx.Graph`.

        Returns:
            NxGraph: The converted graph.
        """
        return SnkitToNxNetworkConverter(
            snkit_network=self.snkit_network,
            node_id_column_name=self.node_id_column_name,
            edge_from_id_column_name=self.edge_from_id_column_name,
            edge_to_id_column_name=self.edge_to_id_column_name,
        ).convert()

    def _aggrfunc(self, cols, attributes_to_exclude: list[str], with_demand: bool):
        def aggregate_column(col_data, col_name: str):
            if col_name in attributes_to_exclude:
                return col_data.iloc[0]
            elif col_name == "rfid_c":
                return list(col_data)
            elif col_name in ["maxspeed", "avgspeed"]:
                return col_data.mean()
            elif with_demand and col_name == "demand_edge":
                return max(col_data)
            elif col_data.dtype == "O":
                col_data_unique_values = list(set(col_data))
                if len(col_data_unique_values) == 1:
                    return col_data_unique_values[0]
                else:
                    return str(col_data_unique_values)
            else:
                return col_data.iloc[0]

        return {
            col: (lambda col_data, col_name=col: aggregate_column(col_data, col_name))
            for col in cols
        }
