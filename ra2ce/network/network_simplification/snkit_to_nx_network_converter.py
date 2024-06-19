from dataclasses import dataclass

import networkx as nx
from snkit.network import Network as SnkitNetwork


@dataclass(kw_only=True)
class SnkitToNxNetworkConverter:
    """
    Class responsible to convert a `snkit.network.Network` into
    a matching `networkx.MultiGraph`.
    """

    snkit_network: SnkitNetwork
    node_id_column_name: str = "id"
    edge_from_id_column_name: str = "from_id"
    edge_to_id_column_name: str = "to_id"

    def convert(self) -> nx.MultiGraph:
        """
        Converts the given `snkit.network.Network` into a matching
        `networkx.MultiGraph`.

        Args:
            snkit_network (SnkitNetwork): The snkit network to convert.

        Returns:
            `networkx.MultiGraph`: The converted graph.
        """
        # Define new graph
        _nx_graph = nx.MultiGraph()
        _crs = self.snkit_network.edges.crs

        # Add nodes to the graph
        for _, row in self.snkit_network.nodes.iterrows():
            node_id = row[self.node_id_column_name]
            attributes = {k: v for k, v in row.items()}
            _nx_graph.add_node(node_id, **attributes)

        # Add edges to the graph
        for _, row in self.snkit_network.edges.iterrows():
            u = row[self.edge_from_id_column_name]
            v = row[self.edge_to_id_column_name]
            attributes = {k: v for k, v in row.items()}
            _nx_graph.add_edge(u, v, **attributes)

        # Add CRS information to the graph
        if "crs" not in _nx_graph.graph:
            _nx_graph.graph["crs"] = _crs

        return _nx_graph
