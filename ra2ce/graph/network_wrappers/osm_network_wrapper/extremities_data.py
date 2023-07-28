from dataclasses import dataclass

from networkx import MultiDiGraph


@dataclass
class ExtremitiesData:
    from_id: int = None
    to_id: int = None
    from_to_id: tuple = None
    to_from_id: tuple = None
    from_to_coor: tuple = None
    to_from_coor: tuple = None

    @staticmethod
    def get_extremities_data_for_sub_graph(
        from_node_id: int,
        to_node_id: int,
        sub_graph: MultiDiGraph,
        graph: MultiDiGraph,
        shared_elements: set,
    ):
        """Both extremities should be in the unique_graph still makes an edge between similar node to u (the node
        with u coordinates and different id, included in the unique_graph) and v Here, sub_graph is the unique_graph
        and graph is complex_graph Shared elements are shared btw sub_graph and graph, which are elements to include
        when dropping duplicates"""
        if shared_elements is None or not isinstance(shared_elements, set):
            raise ValueError("unique_elements should be a set")
        if from_node_id in sub_graph.nodes() and to_node_id in sub_graph.nodes():
            return ExtremitiesData.arrange_extremities_data(
                from_node_id=from_node_id, to_node_id=to_node_id, graph=sub_graph
            )
        elif (
            graph.nodes[from_node_id]["x"],
            graph.nodes[from_node_id]["y"],
        ) in shared_elements and to_node_id in sub_graph.nodes():

            from_node_id_prime = ExtremitiesData.find_node_id_by_coor(
                sub_graph,
                graph.nodes[from_node_id]["x"],
                graph.nodes[from_node_id]["y"],
            )
            if from_node_id_prime == to_node_id:
                return ExtremitiesData()
            else:
                return ExtremitiesData.arrange_extremities_data(
                    from_node_id=from_node_id_prime,
                    to_node_id=to_node_id,
                    graph=sub_graph,
                )

        elif (
            from_node_id in sub_graph.nodes()
            and (graph.nodes[to_node_id]["x"], graph.nodes[to_node_id]["y"])
            in shared_elements
        ):

            to_node_id_prime = ExtremitiesData.find_node_id_by_coor(
                sub_graph, graph.nodes[to_node_id]["x"], graph.nodes[to_node_id]["y"]
            )
            if from_node_id == to_node_id_prime:
                return ExtremitiesData()
            else:
                return ExtremitiesData.arrange_extremities_data(
                    from_node_id=from_node_id,
                    to_node_id=to_node_id_prime,
                    graph=sub_graph,
                )
        else:
            return ExtremitiesData()

    @staticmethod
    def arrange_extremities_data(
        from_node_id: int, to_node_id: int, graph: MultiDiGraph
    ):
        return ExtremitiesData(
            from_id=from_node_id,
            to_id=to_node_id,
            from_to_id=(from_node_id, to_node_id),
            to_from_id=(to_node_id, from_node_id),
            from_to_coor=(
                (graph.nodes[from_node_id]["x"], graph.nodes[to_node_id]["x"]),
                (graph.nodes[from_node_id]["y"], graph.nodes[to_node_id]["y"]),
            ),
            to_from_coor=(
                (graph.nodes[to_node_id]["x"], graph.nodes[from_node_id]["x"]),
                (graph.nodes[to_node_id]["y"], graph.nodes[from_node_id]["y"]),
            ),
        )

    @staticmethod
    def find_node_id_by_coor(graph: MultiDiGraph, target_x: float, target_y: float):
        """
        finds the node in unique graph with the same coor
        """
        for node, data in graph.nodes(data=True):
            if (
                "x" in data
                and "y" in data
                and data["x"] == target_x
                and data["y"] == target_y
            ):
                return node
        return None
