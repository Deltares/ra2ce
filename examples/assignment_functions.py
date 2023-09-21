from typing import Union

import networkx as nx
from matplotlib import pyplot as plt
from networkx import MultiGraph, MultiDiGraph, DiGraph


def _get_directed_graph(graph: MultiGraph) -> MultiDiGraph:
    multi_digraph = nx.MultiDiGraph()
    for u, attr in graph.nodes(data=True):
        if 'geometry' in attr.keys():
            geom = attr['geometry']
            pos = (geom.x, geom.y)
        else:
            pos = ()
        multi_digraph.add_node(u, pos=pos, **attr)
    for u, v, key, attr in graph.edges(keys=True, data=True):
        multi_digraph.add_edge(u, v, **attr)
        multi_digraph.add_edge(v, u, **attr)
    return multi_digraph


def _create_layered_graph(graph: MultiDiGraph) -> MultiDiGraph:
    # ToDo: add all nodes between actual and virtual g
    multi_layer_graph = nx.MultiDiGraph()
    virtual_graph = MultiDiGraph(graph)
    # make costs integer
    for u, attr in graph.nodes(data=True):
        multi_layer_graph.add_node(u, **attr)
    for u, v, key, attr in graph.edges(keys=True, data=True):
        attr['weight'] = int(round(attr['weight'] * 10e6, 0))
        attr['capacity'] = int(attr['capacity'])
        multi_layer_graph.add_edge(u, v, **attr)

    max_weight_graph = max(attr['weight'] for _, _, attr in graph.edges(data=True))
    max_capacity_graph = max(attr['capacity'] for _, _, attr in graph.edges(data=True))

    # add virtual graph to the multi_layer graph
    for u, attr in virtual_graph.nodes(data=True):
        attr = {k: v for k, v in attr.items() if k in attr.keys() and k not in ['demand', 'od_id', 'pos']}
        if 'geometry' in attr.keys():
            geom = attr['geometry']
            pos = (geom.x+10, geom.y+10)
        else:
            pos = ()
        multi_layer_graph.add_node((str(u) + '_d'), pos=pos, **attr)
    for u, v, key, attr in virtual_graph.edges(keys=True, data=True):
        attr['weight'] = int(round(attr['weight'] * 10e6, 0))
        attr['capacity'] = int(max_capacity_graph * 100)
        multi_layer_graph.add_edge((str(u) + '_d'), (str(v) + '_d'), **attr)

    # create links between graph and virtual graph in the multi_layer graph at each node
    for node, attr in graph.nodes(data=True):
        multi_layer_graph.add_edge(node, str(node) + '_d',
                                   weight=max_weight_graph + 1, capacity=max_capacity_graph * 100)
        multi_layer_graph.add_edge(str(node) + '_d', node,
                                   weight=0, capacity=max_capacity_graph * 100)
    return multi_layer_graph


def draw_graph(g: Union[DiGraph, MultiDiGraph]):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    edge_labels = dict([((n1, n2), attr['capacity'])
                        for n1, n2, attr in g.edges(data=True)])
    pos = nx.spring_layout(g)
    nx.draw(g, pos, with_labels=True, arrows=True, node_size=5, node_color='r', font_color='m')
    nx.draw_networkx_edge_labels(
        g, pos,
        edge_labels=edge_labels,
        font_color='red'
    )
    plt.show()
