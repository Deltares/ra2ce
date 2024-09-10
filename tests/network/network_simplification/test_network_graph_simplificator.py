import math
from typing import Callable, Iterator

import networkx as nx
import numpy as np
import pytest
from altgraph.Graph import Graph
from networkx import DiGraph
from shapely.geometry import LineString

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
    def dicts_comparison(
        _graph1: nx.MultiDiGraph | nx.MultiGraph, _graph2: nx.MultiDiGraph | nx.MultiGraph
    ) -> bool:
        for u, v, k, data1 in _graph1.edges(keys=True, data=True):
            geom1 = data1['geometry']
            geom_found = 0

            data2_dict = _graph2.get_edge_data(u, v)
            for _, data2 in data2_dict.items():
                if data2['geometry'] == geom1:
                    geom_found = 1
                    for key1, value1 in data1.items():
                        if key1 not in data2:
                            return False
                        if isinstance(value1, float) and math.isnan(value1):
                            if not math.isnan(data2[key1]):
                                return False
                            continue
                        if value1 != data2[key1]:
                            return False
            if geom_found == 0:
                return False
        return True

    check_1_2 = dicts_comparison(graph1, graph2)
    check_2_1 = dicts_comparison(graph2, graph1)

    if check_1_2 and check_2_1:
        return True
    else:
        return False


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
            _nx_digraph.add_nodes_from([(i, {'x': i, 'y': i * 10}) for i in range(1, 19)])

            _nx_digraph.add_edge(1, 2, a='None')
            _nx_digraph.add_edge(2, 1, a='None')
            _nx_digraph.add_edge(2, 3, a='None')
            _nx_digraph.add_edge(3, 4, a='None')
            _nx_digraph.add_edge(4, 5, a="yes")
            _nx_digraph.add_edge(5, 6, a="yes")
            _nx_digraph.add_edge(6, 7, a="yes")
            _nx_digraph.add_edge(7, 8, a='None')
            _nx_digraph.add_edge(8, 9, a='None')
            _nx_digraph.add_edge(8, 12, a='None')
            _nx_digraph.add_edge(8, 13, a="yes")
            _nx_digraph.add_edge(9, 10, a='None')
            _nx_digraph.add_edge(10, 11, a='None')
            _nx_digraph.add_edge(11, 12, a="yes")
            _nx_digraph.add_edge(13, 14, a="yes")
            _nx_digraph.add_edge(14, 15, a="yes")
            _nx_digraph.add_edge(15, 11, a="yes")
            _nx_digraph.add_edge(1, 16, a='None')
            _nx_digraph.add_edge(16, 1, a='None')
            _nx_digraph.add_edge(16, 17, a='None')
            _nx_digraph.add_edge(16, 18, a='None')

            _nx_digraph = add_missing_geoms_graph(_nx_digraph, "geometry")
            _nx_digraph.graph["crs"] = "EPSG:4326"

            _nx_digraph = add_missing_geoms_graph(_nx_digraph, "geometry")
            return _nx_digraph

        yield create_nx_multidigraph

    @pytest.fixture(name="expected_result_graph_fixture")
    def _get_expected_result_graph_fixture(
        self, nx_digraph_factory: nx.MultiDiGraph
    ) -> nx.MultiGraph:
        def add_edge_with_attributes(graph_to_shape: Graph | DiGraph, edge_u: int | float, edge_v: int | float, a_value: str, edge_node_ids: list) -> Graph | DiGraph:
            # Create a copy of the input graph
            shaped_graph = graph_to_shape.copy()

            # Extract geometries programmatically using edge_node_ids
            geometry_list = [graph_to_shape.nodes[n_id]["geometry"] for n_id in edge_node_ids]

            shaped_graph.add_edge(
                edge_u,
                edge_v,
                a=a_value,
                from_node=edge_u,
                to_node=edge_v,
                geometry=LineString(geometry_list),
            )
            return shaped_graph

        _nx_digraph = nx_digraph_factory()
        _result_digraph = nx.MultiDiGraph()
        node_ids_degrees = {2: 3, 4: 2, 7: 2, 8: 4, 11: 3, 12: 2, 16: 4, 17: 1, 18: 1}
        for node_id, degree in node_ids_degrees.items():
            node_data = _nx_digraph.nodes[node_id]
            node_data["id"] = node_id
            node_data["degree"] = degree
            _result_digraph.add_node(node_id, **node_data)
        _result_digraph = add_missing_geoms_graph(_result_digraph, "geometry")

        _result_digraph = add_edge_with_attributes(
            _result_digraph, 2, 4.0, 'None', [2, 3, 4]
        )
        _result_digraph = add_edge_with_attributes(
            _result_digraph, 2, 16.0, 'None', [2, 1, 16]
        )
        _result_digraph = add_edge_with_attributes(
            _result_digraph, 4, 7.0, 'yes', [4, 5, 6, 7]
        )
        _result_digraph = add_edge_with_attributes(
            _result_digraph, 7, 8.0, 'None', [7, 8]
        )
        _result_digraph = add_edge_with_attributes(
            _result_digraph, 8, 11, 'None', [8, 9, 10, 11]
        )
        _result_digraph = add_edge_with_attributes(
            _result_digraph, 8, 11, 'yes', [8, 13, 14, 15, 11]
        )
        _result_digraph = add_edge_with_attributes(
            _result_digraph, 8, 12, 'None', [8, 12]
        )
        _result_digraph = add_edge_with_attributes(
            _result_digraph, 11, 12, 'yes', [11, 12]
        )
        _result_digraph = add_edge_with_attributes(
            _result_digraph, 16, 2.0, 'None', [16, 1, 2]
        )
        _result_digraph = add_edge_with_attributes(
            _result_digraph, 16, 17, 'None', [16, 17]
        )
        _result_digraph = add_edge_with_attributes(
            _result_digraph, 16, 18, 'None', [16, 18]
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
        # Compare edges with attributes
        assert _detailed_edge_comparison(_graph_simple, expected_result_graph_fixture)
