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
    multi_layer_graph = nx.MultiDiGraph()
    virtual_graph = MultiDiGraph(graph)
    # make costs integer
    for u, v, key, attr in graph.edges(keys=True, data=True):
        attr['cost'] = round(attr['cost']*10e10, 0)
        multi_layer_graph.add_edge(u, v, **attr)
    for u, attr in graph.nodes(data=True):
        multi_layer_graph.add_node(u, **attr)

    max_node_id_graph = max(graph.nodes())
    max_cost_graph = max(attr['cost'] for _, _, attr in graph.edges(data=True))
    max_capacity_graph = max(attr['capacity'] for _, _, attr in graph.edges(data=True))

    # add virtual graph to the multi_layer graph
    for u, attr in virtual_graph.nodes(data=True):
        attr = {k: v for k, v in attr.items() if k in attr.keys() and k not in ['demand', 'od_id']}
        multi_layer_graph.add_node(u + max_node_id_graph, **attr)
    for u, v, key, attr in virtual_graph.edges(keys=True, data=True):
        attr['cost'] = round(attr['cost'] * 10e10, 0)
        attr['capacity'] = max_capacity_graph * 100
        multi_layer_graph.add_edge(u + max_node_id_graph, v + max_node_id_graph, **attr)
    # create links between graph and virtual graph in the multi_layer graph
    od_node_list = [n for n in graph.nodes(data=True) if "od_id" in n[-1]]
    for od_node in od_node_list:
        od_node_id_graph = od_node[0]
        od_node_id_virtual_graph = od_node[0] + max_node_id_graph
        multi_layer_graph.add_edge(od_node_id_graph, od_node_id_virtual_graph,
                                   cost=max_cost_graph + 1, capacity=max_capacity_graph * 100)
        multi_layer_graph.add_edge(od_node_id_virtual_graph, od_node_id_graph,
                                   cost=0, capacity=max_capacity_graph * 100)
    return multi_layer_graph

# ToDo: make all floating points numbers integer (cost)
