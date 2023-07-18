import pandas as pd
from ra2ce.analyses.indirect.accumulated_traffic_dataclass import AccumulatedTraffic


class EquityTrafficDataWrapper:
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
    def get_node_key(left_node: str, right_node: str) -> str:
        """
        Gets the string representation of the combination of two nodes.

        Args:
            left_node (str): 'u' node.
            right_node (str): 'v' node.

        Returns:
            str: Name for the combination of two nodes.
        """
        return f"{left_node}_{right_node}"

    def add_visited_nodes(self, left_node: str, right_node: str) -> str:
        """
        Generates a node label and adds the provided nodes to a list of `visited` nodes.

        Args:
            left_node (str): Represents the `u` node.
            right_node (str): Represents the `v` node.

        Returns:
            str: The combined node names.
        """
        _node_key = self.get_node_key(left_node, right_node)
        self._visited_nodes.append((left_node, right_node))
        return _node_key

    def update_traffic_routes(
        self, nodes_key: str, accumulated_traffic: AccumulatedTraffic
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
        u_list, v_list = zip(*self._visited_nodes)
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
