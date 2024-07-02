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
from dataclasses import dataclass

import networkx as nx
from osmnx.simplification import simplify_graph

from ra2ce.network.networks_utils import add_x_y_to_nodes

NxGraph = nx.Graph | nx.MultiGraph | nx.MultiDiGraph


@dataclass(kw_only=True)
class NetworkSimplificationWithoutAttributeExclusion:
    """
    Simplifies a network with the `osmnx.simplification` functionality.
    """

    nx_graph: NxGraph

    def simplify_graph(
        self,
    ) -> nx.Graph:
        """
        Simplify the graph after adding missing x and y attributes to nodes

        Returns:
            nx.Graph: Simplified graph
        """
        _complex_graph = add_x_y_to_nodes(self.nx_graph)
        _simple_graph = simplify_graph(
            _complex_graph, strict=True, remove_rings=True, track_merged=False
        )

        logging.info(
            "Graph simplified from %s to %s nodes and %s to %s edges.",
            _complex_graph.number_of_nodes(),
            _simple_graph.number_of_nodes(),
            _complex_graph.number_of_edges(),
            _simple_graph.number_of_edges(),
        )

        return _simple_graph
