from typing import Iterator

import networkx as nx
import pytest

from ra2ce.network.network_simplification.network_graph_simplificator import (
    NetworkGraphSimplificator,
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
