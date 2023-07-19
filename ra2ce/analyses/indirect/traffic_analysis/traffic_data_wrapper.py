from dataclasses import dataclass, field
import pandas as pd
from ra2ce.analyses.indirect.traffic_analysis.accumulated_traffic_dataclass import (
    AccumulatedTaffic,
)


@dataclass
class TrafficDataWrapper:
    regular: dict = field(default_factory={})
    egalitarian: dict = field(default_factory={})
    prioritarian: dict = field(default_factory={})

    @staticmethod
    def get_node_key(u_node: str, v_node: str) -> str:
        """
        Gets the string representation of the combination of two nodes.

        Args:
            u_node (str): 'u' node.
            v_node (str): 'v' node.

        Returns:
            str: Name for the combination of two nodes.
        """
        return f"{u_node}_{v_node}"

    @staticmethod
    def get_key_nodes(node_key: str) -> tuple[str, str]:
        """
        Gets the nodes represented by the provided `node_key`.

        Args:
            node_key (str): Node key representing `u_node` and `v_node`.

        Returns:
            tuple[str, str]: Values for the `u_node` and `v_node`.
        """
        return node_key.split("_")

    def _get_accumulated_data(self, node_key: str) -> AccumulatedTaffic:
        """
        Gets the accumulated traffic data structure (`AccumulatedTraffic`) for the requested node `node_key`.

        Args:
            node_key (str): Node key whose accumulated traffic is requested.

        Returns:
            AccumulatedTaffic: Accumulated traffic values or with zeros if the `node_key` is not present.
        """
        if node_key not in self.regular.keys():
            return AccumulatedTaffic(regular=0, egalitarian=0, prioritarian=0)
        return AccumulatedTaffic(
            regular=self.regular[node_key],
            egalitarian=self.egalitarian[node_key],
            prioritarian=self.prioritarian[node_key],
        )

    def update_traffic_routes(
        self, nodes_key: str, traffic_values: AccumulatedTaffic
    ) -> None:
        """
        Updates the traffic dictionaries based on the provided accumulated traffic.

        Args:
            nodes_key (str): Node whose traffic data is provided.
            traffic_values (AccumulatedTraffic): Traffic data for regular, egalitarian and prioritarian traffic.
        """
        _accumulated_traffic = self._get_accumulated_data(nodes_key) + traffic_values
        self.regular[nodes_key] = _accumulated_traffic.regular
        self.egalitarian[nodes_key] = _accumulated_traffic.egalitarian
        self.prioritarian[nodes_key] = _accumulated_traffic.egalitarian
