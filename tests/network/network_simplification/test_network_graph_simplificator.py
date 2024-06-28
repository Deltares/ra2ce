import random
from typing import Callable, Iterator

import networkx as nx
import numpy as np
import pytest
from shapely.geometry import LineString, Point

from ra2ce.network import add_missing_geoms_graph
from ra2ce.network.network_simplification.network_graph_simplificator import (
    NetworkGraphSimplificator,
)
from ra2ce.network.network_simplification.network_simplification_with_attribute_exclusion import (
    NetworkSimplificationWithAttributeExclusion,
)
from ra2ce.network.network_simplification.nx_to_snkit_network_converter import (
    NxToSnkitNetworkConverter,
)
from ra2ce.network.network_simplification.snkit_to_nx_network_converter import (
    SnkitToNxNetworkConverter,
)
from ra2ce.network.networks_utils import line_length


def _detailed_edge_comparison(
    graph1: nx.MultiDiGraph | nx.MultiGraph, graph2: nx.MultiDiGraph | nx.MultiGraph
) -> bool:
    for u, v, k, data in graph1.edges(keys=True, data=True):
        if data != graph2.get_edge_data(u, v, k):
            return False

    for u, v, k, data in graph2.edges(keys=True, data=True):
        if data != graph1.get_edge_data(u, v, k):
            return False

    return True


class TestNetworkGraphSimplificator:
    @pytest.fixture(name="network_graph_simplificator_factory")
    def _get_network_graph_simplificator(
        self,
    ) -> Iterator[Callable[[], NetworkGraphSimplificator]]:
        def get_network_graph_simplificator() -> NetworkGraphSimplificator:
            return NetworkGraphSimplificator(
                graph_complex=None, attributes_to_exclude=[]
            )

        yield get_network_graph_simplificator

    def test_validate_fixture_init(
        self,
        network_graph_simplificator_factory: Callable[[], NetworkGraphSimplificator],
    ):
        # 1. Define test data.
        _network_graph_simplificator = network_graph_simplificator_factory()

        # 2. Verify expectations
        assert isinstance(_network_graph_simplificator, NetworkGraphSimplificator)

    @pytest.fixture(name="multigraph_fixture")
    def _get_multigraph_fixture(self) -> Iterator[nx.MultiGraph]:
        _graph = nx.MultiGraph()
        _graph.add_edge(2, 3, weight=5)
        _graph.add_edge(2, 1, weight=2)
        yield _graph

    def test__graph_create_unique_ids_with_missing_id_data(
        self,
        network_graph_simplificator_factory: Callable[[], NetworkGraphSimplificator],
        multigraph_fixture: nx.MultiGraph,
    ):
        # 1. Define test data
        _network_graph_simplificator = network_graph_simplificator_factory()
        assert isinstance(multigraph_fixture, nx.MultiGraph)
        _new_id_name = "dummy_id"

        # 2. Run test
        _return_graph = _network_graph_simplificator._graph_create_unique_ids(
            multigraph_fixture, _new_id_name
        )

        # 3. Verify final expectations
        assert _return_graph == multigraph_fixture
        _dicts_keys = [_k[-1].keys() for _k in multigraph_fixture.edges.data(keys=True)]
        assert all(_new_id_name in _keys for _keys in _dicts_keys)

    def test__graph_create_unique_ids_with_existing_id(
        self,
        network_graph_simplificator_factory: NetworkGraphSimplificator,
        multigraph_fixture: nx.MultiGraph,
    ):
        # 1. Define test data
        _network_graph_simplificator = network_graph_simplificator_factory()
        assert isinstance(multigraph_fixture, nx.MultiGraph)
        _new_id_name = "weight"

        # 2. Run test
        _return_graph = _network_graph_simplificator._graph_create_unique_ids(
            multigraph_fixture, _new_id_name
        )

        # 3. Verify final expectations
        assert _return_graph == multigraph_fixture


class TestNetworkSimplificationWithAttributeExclusion:
    @pytest.fixture(name="network_simplification_with_attribute_exclusion")
    def _get_network_simplification_with_attribute_exclusion(
        self,
    ) -> Iterator[NetworkSimplificationWithAttributeExclusion]:
        yield NetworkSimplificationWithAttributeExclusion(
            nx_graph=None, attributes_to_exclude=[]
        )

    @pytest.fixture(name="nx_digraph_factory")
    def _get_nx_digraph_factory(self) -> Iterator[Callable[[], nx.MultiDiGraph]]:
        def create_nx_multidigraph():
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

            _nx_digraph = add_missing_geoms_graph(_nx_digraph, "geometry")
            return _nx_digraph

        yield create_nx_multidigraph

    @pytest.fixture(name="expected_result_graph_fixture")
    def _get_expected_result_graph_fixture(
        self, nx_digraph_factory: nx.MultiDiGraph
    ) -> nx.MultiGraph:
        _nx_digraph = nx_digraph_factory()
        _result_digraph = nx.MultiGraph()
        node_ids_degrees = {2: 1, 4: 2, 7: 2, 8: 4, 11: 3, 12: 2}
        for node_id, degree in node_ids_degrees.items():
            node_data = _nx_digraph.nodes[node_id]
            node_data["id"] = node_id
            node_data["degree"] = degree
            _result_digraph.add_node(node_id, **node_data)
        _result_digraph = add_missing_geoms_graph(_result_digraph, "geometry")

        _result_digraph.add_edge(
            2,
            4.0,
            a="None",
            from_node=2,
            to_node=4,
            geometry=LineString(
                [
                    _nx_digraph.nodes[2]["geometry"],
                    _nx_digraph.nodes[3]["geometry"],
                    _nx_digraph.nodes[4]["geometry"],
                ]
            ),
        )

        _result_digraph.add_edge(
            4,
            7.0,
            a="yes",
            from_node=4,
            to_node=7,
            geometry=LineString(
                [
                    _nx_digraph.nodes[4]["geometry"],
                    _nx_digraph.nodes[5]["geometry"],
                    _nx_digraph.nodes[6]["geometry"],
                    _nx_digraph.nodes[7]["geometry"],
                ]
            ),
        )
        _result_digraph.add_edge(
            7,
            8.0,
            a="None",
            from_node=7,
            to_node=8,
            geometry=LineString(
                [
                    _nx_digraph.nodes[7]["geometry"],
                    _nx_digraph.nodes[8]["geometry"],
                ]
            ),
        )
        _result_digraph.add_edge(
            8,
            11.0,
            a="None",
            from_node=8,
            to_node=11,
            geometry=LineString(
                [
                    _nx_digraph.nodes[8]["geometry"],
                    _nx_digraph.nodes[9]["geometry"],
                    _nx_digraph.nodes[10]["geometry"],
                    _nx_digraph.nodes[11]["geometry"],
                ]
            ),
        )
        _result_digraph.add_edge(
            8,
            11.0,
            a="yes",
            from_node=8,
            to_node=11,
            geometry=LineString(
                [
                    _nx_digraph.nodes[8]["geometry"],
                    _nx_digraph.nodes[13]["geometry"],
                    _nx_digraph.nodes[14]["geometry"],
                    _nx_digraph.nodes[15]["geometry"],
                    _nx_digraph.nodes[11]["geometry"],
                ]
            ),
        )
        _result_digraph.add_edge(
            8,
            12.0,
            a="None",
            from_node=8,
            to_node=12,
            geometry=LineString(
                [
                    _nx_digraph.nodes[8]["geometry"],
                    _nx_digraph.nodes[12]["geometry"],
                ]
            ),
        )
        _result_digraph.add_edge(
            11,
            12.0,
            a="yes",
            from_node=11,
            to_node=12,
            geometry=LineString(
                [
                    _nx_digraph.nodes[11]["geometry"],
                    _nx_digraph.nodes[12]["geometry"],
                ]
            ),
        )

        _result_digraph.graph["crs"] = "EPSG:4326"

        snkit_network = NxToSnkitNetworkConverter(
            networkx_graph=_result_digraph
        ).convert()
        snkit_network.edges["length"] = snkit_network.edges["geometry"].apply(
            lambda x: line_length(x, snkit_network.edges.crs)
        )
        snkit_network.edges = snkit_network.edges.drop(
            columns=["id", "from_node", "to_node"]
        )
        return SnkitToNxNetworkConverter(snkit_network=snkit_network).convert()

    def test_simplify_graph(
        self,
        network_simplification_with_attribute_exclusion: NetworkSimplificationWithAttributeExclusion,
        nx_digraph_factory: Callable[[], nx.MultiDiGraph],
        expected_result_graph_fixture: nx.MultiDiGraph,
    ):
        network_simplification_with_attribute_exclusion.nx_graph = nx_digraph_factory()
        network_simplification_with_attribute_exclusion.attributes_to_exclude = ["a"]

        _graph_simple = network_simplification_with_attribute_exclusion.simplify_graph()

        # Compare nodes with attributes
        assert _graph_simple.nodes(data=True) == expected_result_graph_fixture.nodes(
            data=True
        )
        # Compare edges topology
        assert set(_graph_simple.edges()) == set(expected_result_graph_fixture.edges())
        # Compare edges with attributes
        assert _detailed_edge_comparison(_graph_simple, expected_result_graph_fixture)
