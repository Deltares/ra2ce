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
from tqdm import tqdm

from ra2ce.network.network_simplification.network_simplification_with_attribute_exclusion import (
    NetworkSimplificationWithAttributeExclusion,
)
from ra2ce.network.networks_utils import add_x_y_to_nodes

NxGraph = nx.Graph | nx.MultiGraph | nx.MultiDiGraph


def graph_link_simple_id_to_complex(graph_simple: nx.classes.graph.Graph, new_id: str):
    """
    Create lookup tables (dicts) to match edges_ids of the complex and simple graph
    Optionally, saves these lookup tables as json files.

    Arguments:
        graph_simple (Graph) : Graph, containing attribute 'new_id'
        new_id (string) : Name of the ID attribute in graph_simple

    Returns:
        simple_to_complex (dict): Keys are ids of the simple graph, values are lists with all matching complex ids
        complex_to_simple (dict): Keys are the ids of the complex graph, value is the matching simple_ID

    We need this because the simple graph is derived from the complex graph, and therefore initially only the
    simple graph knows from which complex edges it was created. To assign this information also to the complex
    graph we invert the look-up dictionary
    @author: Kees van Ginkel en Margreet van Marle
    """
    # Iterate over the simple, because this already has the corresponding complex information
    lookup_dict = {}
    # keys are the ids of the simple graph, values are lists with all matching complex id's
    for u, v, k in tqdm(graph_simple.edges(keys=True)):
        key_1 = graph_simple[u][v][k]["{}".format(new_id)]
        value_1 = graph_simple[u][v][k]["{}_c".format(new_id)]
        lookup_dict[key_1] = value_1

    inverted_lookup_dict = {}
    # keys are the ids of the complex graph, value is the matching simple_ID
    for key, value in lookup_dict.items():
        if isinstance(value, list):
            for subvalue in value:
                inverted_lookup_dict[subvalue] = key
        elif isinstance(value, int):
            inverted_lookup_dict[value] = key

    simple_to_complex = lookup_dict
    complex_to_simple = inverted_lookup_dict

    logging.info("Lookup tables from complex to simple and vice versa were created")
    return simple_to_complex, complex_to_simple


@dataclass(kw_only=True)
class NetworkSimplificationFactory:
    """
    Factory dataclass to simplify the containing graph.
    """

    graph_complex: NxGraph
    attributes_to_exclude: list[str]
    new_id: str = "rfid"

    def simplify_graph(
        self,
    ) -> tuple[nx.Graph, nx.Graph, tuple[dict, dict]]:
        """Create a simplified graph with unique ids from a complex graph"""
        logging.info("Simplifying graph")
        try:
            _graph_complex = self._graph_create_unique_ids(
                self.graph_complex, "{}_c".format(self.new_id)
            )
            if any(self.attributes_to_exclude):
                _graph_simple = NetworkSimplificationWithAttributeExclusion(
                    nx_graph=self.graph_complex,
                    attributes_to_exclude=self.attributes_to_exclude,
                ).simplify_graph()
            else:
                # Create simplified graph and add unique ids
                _graph_simple = self._simplify_graph_count_without_attribute_exclusion(
                    _graph_complex
                )

            _graph_simple = self._graph_create_unique_ids(_graph_simple, self.new_id)

            # Create look_up_tables between graphs with unique ids
            _simple_to_complex, _complex_to_simple = graph_link_simple_id_to_complex(
                _graph_simple, new_id=self.new_id
            )

            # Store id table and add simple ids to complex graph
            _id_tables = (_simple_to_complex, _complex_to_simple)
            _graph_complex = self._add_simple_id_to_graph_complex(
                _graph_complex, _complex_to_simple, self.new_id
            )
            logging.info("Simplified graph successfully created")
        except Exception as exc:
            _graph_simple = None
            _id_tables = None
            logging.error("Did not create a simplified version of the graph (%s)", exc)
        return _graph_simple, _graph_complex, _id_tables

    def _graph_create_unique_ids(
        self, graph: nx.Graph, new_id_name: str = "rfid"
    ) -> nx.Graph:
        # Check if new_id_name exists and if unique
        u, v, k = list(graph.edges)[0]
        if new_id_name in graph.edges[u, v, k]:
            return graph
        # TODO: decide if we always add a new ID (in iGraph this is different)
        # if len(set([str(e[-1][new_id_name]) for e in graph.edges.data(keys=True)])) < len(graph.edges()):
        for i, (u, v, k) in enumerate(graph.edges(keys=True)):
            graph[u][v][k][new_id_name] = i + 1
        logging.info("Added a new unique identifier field '%s'.", new_id_name)
        return graph

    def _add_simple_id_to_graph_complex(
        self, complex_graph: nx.classes.Graph, complex_to_simple, new_id
    ) -> nx.classes.Graph:
        """Adds the appropriate ID of the simple graph to each edge of the complex graph as a new attribute 'rfid'

        Arguments:
            complex_graph (Graph) : The complex graph, still lacking 'rfid'
            complex_to_simple (dict) : lookup table linking complex to simple graphs

        Returns:
            complex_graph (Graph) : Same object, with added attribute 'rfid'

        """

        obtained_complex_ids = nx.get_edge_attributes(
            complex_graph, "{}_c".format(new_id)
        )  # {(u,v,k) : 'rfid_c'}
        simple_ids_per_complex_id = obtained_complex_ids  # start with a copy

        for key, value in obtained_complex_ids.items():  # {(u,v,k) : 'rfid_c'}
            try:
                new_value = complex_to_simple[
                    value
                ]  # find simple id belonging to the complex id
                simple_ids_per_complex_id[key] = new_value
            except KeyError as e:
                logging.error(
                    "Could not find the simple ID belonging to complex ID %s; value set to None. Full error: %s",
                    key,
                    e,
                )
                simple_ids_per_complex_id[key] = None

        # Now the format of simple_ids_per_complex_id is: {(u,v,k) : 'rfid}
        nx.set_edge_attributes(complex_graph, simple_ids_per_complex_id, new_id)

        return complex_graph

    def _simplify_graph_count_without_attribute_exclusion(
        self,
        complex_graph: nx.Graph,
    ) -> nx.Graph:
        """
        Simplify the graph after adding missing x and y attributes to nodes

        Args:
            complex_graph (nx.Graph): Graph to simplify

        Returns:
            nx.Graph: Simplified graph
        """
        complex_graph = add_x_y_to_nodes(complex_graph)
        simple_graph = simplify_graph(
            complex_graph, strict=True, remove_rings=True, track_merged=False
        )

        logging.info(
            "Graph simplified from %s to %s nodes and %s to %s edges.",
            complex_graph.number_of_nodes(),
            simple_graph.number_of_nodes(),
            complex_graph.number_of_edges(),
            simple_graph.number_of_edges(),
        )

        return simple_graph
