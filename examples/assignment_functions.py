import networkx as nx
from networkx import MultiGraph, MultiDiGraph


def _get_directed_graph(graph: MultiGraph) -> MultiDiGraph:
    multi_digraph = nx.MultiDiGraph()
    for u, v, key, attr in graph.edges(keys=True, data=True):
        multi_digraph.add_edge(u, v, **attr)
    for u, attr in graph.nodes(data=True):
        multi_digraph.add_node(u, **attr)
    return multi_digraph


def _create_layered_graph(graph: MultiDiGraph) -> MultiDiGraph:
    multi_digraph = nx.MultiDiGraph()
    virtual_graph = MultiDiGraph(graph)
    od_node_list = [n for n in graph.nodes(data=True) if "od_id" in n[-1]]
    for od_node in od_node_list:

    return multi_digraph
