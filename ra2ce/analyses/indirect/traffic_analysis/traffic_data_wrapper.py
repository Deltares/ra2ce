import pandas as pd
from ra2ce.analyses.indirect.traffic_analysis.accumulated_traffic_dataclass import (
    AccumulatedTaffic,
)


class TrafficDataWrapper:
    regular: dict
    egalitarian: dict
    prioritarian: dict
    with_equity: bool

    def __init__(self) -> None:
        self.regular = {}
        self.egalitarian = {}
        self.prioritarian = {}
        self.with_equity = False
        self._visited_nodes = []

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

    def update_traffic_routes(
        self, nodes_key: str, accumulated_traffic: AccumulatedTaffic
    ) -> None:
        """
        Updates the traffic dictionaries based on the provided accumulated traffic.

        Args:
            nodes_key (str): Node whose traffic data is provided.
            accumulated_traffic (AccumulatedTraffic): Traffic data for regular, egalitarian and prioritarian traffic.
        """
        self.regular[nodes_key] = accumulated_traffic.regular + self.regular.get(
            nodes_key, 0
        )
        self.egalitarian[
            nodes_key
        ] = accumulated_traffic.egalitarian + self.egalitarian.get(nodes_key, 0)
        if self.with_equity:
            self.prioritarian[
                nodes_key
            ] = accumulated_traffic.prioritarian + self.prioritarian.get(nodes_key, 0)

    def get_route_traffic(self) -> pd.DataFrame:
        """
        Combines all the `visited_nodes` with the traffic data stored in the internal dictionaries for `regular`, `egalitarian` and `prioritarian` traffic.

        Returns:
            pd.DataFrame: Resulting dataframe with all traffic data.
        """
        u_list, v_list = zip(*map(self.get_key_nodes, self.regular))
        t_list = self.regular.values()
        teq_list = self.egalitarian.values()

        if not self.with_equity:
            data_tuples = list(zip(u_list, v_list, t_list, teq_list))
            return pd.DataFrame(
                data_tuples, columns=["u", "v", "traffic", "traffic_egalitarian"]
            )

        data_tuples = list(
            zip(u_list, v_list, t_list, teq_list, self.prioritarian.values())
        )
        return pd.DataFrame(
            data_tuples,
            columns=[
                "u",
                "v",
                "traffic",
                "traffic_egalitarian",
                "traffic_prioritarian",
            ],
        )
