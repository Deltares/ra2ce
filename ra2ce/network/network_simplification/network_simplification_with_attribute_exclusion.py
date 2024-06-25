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

from dataclasses import dataclass

import networkx as nx

from ra2ce.network.network_simplification.snkit_network_wrapper import (
    SnkitNetworkWrapper,
)

NxGraph = nx.Graph | nx.MultiGraph | nx.MultiDiGraph


@dataclass(kw_only=True)
class NetworkSimplificationWithAttributeExclusion:
    """
    Simplifies a network by excluding a given set of attributes (columns).
    """

    nx_graph: NxGraph
    attributes_to_exclude: list[str]

    def simplify_graph(self) -> nx.Graph:
        """
        Simplifies the inner graph by using the `snkit` package.

        Returns:
            nx.Graph: Resulting simplified graph.
        """
        _snkit_network_wrapper = SnkitNetworkWrapper.from_networkx(
            self.nx_graph,
            column_names_dict=dict(
                node_id_column_name="id",
                edge_from_id_column_name="from_id",
                edge_to_id_column_name="to_id",
            ),
        )
        _snkit_network_wrapper.merge_edges(self.attributes_to_exclude)
        _snkit_network_wrapper.process_network()
        return _snkit_network_wrapper.to_networkx()
