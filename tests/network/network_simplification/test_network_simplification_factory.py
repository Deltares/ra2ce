from typing import Iterator

import networkx as nx
import pytest

from ra2ce.network.network_simplification.network_simplification_factory import (
    NetworkSimplificationFactory,
)


class TestNetworkSimplificationFactory:
    @pytest.fixture(name="network_simplification_factory")
    def _get_network_simplification_factory(
        self,
    ) -> Iterator[NetworkSimplificationFactory]:
        yield NetworkSimplificationFactory(graph_complex=None, attributes_to_exclude=[])

    def test_validate_fixture_init(
        self,
        network_simplification_factory: NetworkSimplificationFactory,
    ):
        assert isinstance(network_simplification_factory, NetworkSimplificationFactory)

    def test__graph_create_unique_ids_with_missing_id_data(
        self, network_simplification_factory: NetworkSimplificationFactory
    ):
        # 1. Define test data
        _graph = nx.MultiGraph()
        _graph.add_edge(2, 3, weight=5)
        _graph.add_edge(2, 1, weight=2)
        _new_id_name = "dummy_id"

        # 2. Run test
        _return_graph = network_simplification_factory._graph_create_unique_ids(
            _graph, _new_id_name
        )

        # 3. Verify final expectations
        assert _return_graph == _graph
        _dicts_keys = [_k[-1].keys() for _k in _graph.edges.data(keys=True)]
        assert all(_new_id_name in _keys for _keys in _dicts_keys)

    def test__graph_create_unique_ids_with_existing_id(
        self, network_simplification_factory: NetworkSimplificationFactory
    ):
        # 1. Define test data
        _graph = nx.MultiGraph()
        _graph.add_edge(2, 3, weight=5)
        _graph.add_edge(2, 1, weight=2)
        _new_id_name = "weight"

        # 2. Run test
        _return_graph = network_simplification_factory._graph_create_unique_ids(
            _graph, _new_id_name
        )

        # 3. Verify final expectations
        assert _return_graph == _graph
