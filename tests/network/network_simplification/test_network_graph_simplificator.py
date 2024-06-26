import random
from typing import Iterator

import networkx as nx
import numpy as np
import pytest

from ra2ce.network import add_missing_geoms_graph
from ra2ce.network.network_simplification.network_graph_simplificator import (
    NetworkGraphSimplificator,
)
from ra2ce.network.network_simplification.network_simplification_with_attribute_exclusion import (
    NetworkSimplificationWithAttributeExclusion,
)


class TestNetworkGraphSimplificator:
    @pytest.fixture(name="network_graph_simplificator")
    def _get_network_graph_simplificator(
        self,
    ) -> Iterator[NetworkGraphSimplificator]:
        yield NetworkGraphSimplificator(graph_complex=None, attributes_to_exclude=[])

    def test_validate_fixture_init(
        self,
        network_graph_simplificator: NetworkGraphSimplificator,
    ):
        assert isinstance(network_graph_simplificator, NetworkGraphSimplificator)

    def test__graph_create_unique_ids_with_missing_id_data(
        self, network_graph_simplificator: NetworkGraphSimplificator
    ):
        # 1. Define test data
        _graph = nx.MultiGraph()
        _graph.add_edge(2, 3, weight=5)
        _graph.add_edge(2, 1, weight=2)
        _new_id_name = "dummy_id"

        # 2. Run test
        _return_graph = network_graph_simplificator._graph_create_unique_ids(
            _graph, _new_id_name
        )

        # 3. Verify final expectations
        assert _return_graph == _graph
        _dicts_keys = [_k[-1].keys() for _k in _graph.edges.data(keys=True)]
        assert all(_new_id_name in _keys for _keys in _dicts_keys)

    def test__graph_create_unique_ids_with_existing_id(
        self, network_graph_simplificator: NetworkGraphSimplificator
    ):
        # 1. Define test data
        _graph = nx.MultiGraph()
        _graph.add_edge(2, 3, weight=5)
        _graph.add_edge(2, 1, weight=2)
        _new_id_name = "weight"

        # 2. Run test
        _return_graph = network_graph_simplificator._graph_create_unique_ids(
            _graph, _new_id_name
        )

        # 3. Verify final expectations
        assert _return_graph == _graph


class TestNetworkSimplificationWithAttributeExclusion:
    @pytest.fixture(name="network_simplification_with_attribute_exclusion")
    def _get_network_simplification_with_attribute_exclusion(
        self,
    ) -> Iterator[NetworkSimplificationWithAttributeExclusion]:
        yield NetworkSimplificationWithAttributeExclusion(
            nx_graph=None, attributes_to_exclude=[]
        )

    @pytest.fixture(name="random_integer")
    def random_integer(self) -> int:
        random_int = random.randint(0, 5) * random.choice([-1, 1])
        return random_int

    @pytest.fixture(name="_nx_digraph")
    def _nx_digraph_fixture(self, random_integer: int) -> nx.MultiDiGraph:
        _nx_digraph = nx.MultiDiGraph()
        for i in range(1, 16):
            random_x = random.randint(0, 5) * random.choice([-1, 1])
            random_y = random.randint(0, 5) * random.choice([-1, 1])
            _nx_digraph.add_node(i, x=random_x, y=random_y)

        _nx_digraph.add_edge(1, 2, a=np.nan)
        _nx_digraph.add_edge(2, 1, a=np.nan)
        _nx_digraph.add_edge(2, 3, a=np.nan)
        _nx_digraph.add_edge(3, 4, a=np.nan)
        _nx_digraph.add_edge(4, 5, a="yes")
        _nx_digraph.add_edge(5, 6, a="yes")
        _nx_digraph.add_edge(6, 7, a="yes")
        _nx_digraph.add_edge(7, 8, a=np.nan)
        _nx_digraph.add_edge(8, 9, a=np.nan)
        _nx_digraph.add_edge(8, 12, a=np.nan)
        _nx_digraph.add_edge(8, 13, a="yes")
        _nx_digraph.add_edge(9, 10, a=np.nan)
        _nx_digraph.add_edge(10, 11, a=np.nan)
        _nx_digraph.add_edge(11, 12, a="yes")
        _nx_digraph.add_edge(13, 14, a="yes")
        _nx_digraph.add_edge(14, 15, a="yes")
        _nx_digraph.add_edge(15, 11, a="yes")

        _nx_digraph = add_missing_geoms_graph(_nx_digraph, "geometry")
        _nx_digraph.graph["crs"] = "EPSG:4326"
        return _nx_digraph

    @pytest.fixture(name="_result_digraph")
    def _result_digraph_fixture(self, _nx_digraph: nx.MultiDiGraph) -> nx.MultiDiGraph:
        _result_digraph = nx.MultiDiGraph()
        for node_id in [2, 4, 7, 8, 11, 12]:
            node_data = _nx_digraph.nodes[node_id]
            node_data["id"] = node_id
            _result_digraph.add_node(node_id, **node_data)
        _result_digraph.add_edge(2, 4, a=np.nan)
        _result_digraph.add_edge(4, 7, a="yes")
        _result_digraph.add_edge(7, 8, a=np.nan)
        _result_digraph.add_edge(8, 11, a=np.nan)
        _result_digraph.add_edge(8, 11, a="yes")
        _result_digraph.add_edge(8, 12, a=np.nan)
        _result_digraph.add_edge(11, 12, a="yes")

        _result_digraph = add_missing_geoms_graph(_result_digraph, "geometry")
        _result_digraph.graph["crs"] = "EPSG:4326"
        return _result_digraph

    def test_simplify_graph(
        self,
        _nx_digraph: nx.MultiDiGraph,
        _result_digraph: nx.MultiDiGraph,
        network_simplification_with_attribute_exclusion: NetworkSimplificationWithAttributeExclusion,
    ):
        network_simplification_with_attribute_exclusion.nx_graph = _nx_digraph
        network_simplification_with_attribute_exclusion.attributes_to_exclude = ["a"]
        _graph_simple = network_simplification_with_attribute_exclusion.simplify_graph()
        pass
