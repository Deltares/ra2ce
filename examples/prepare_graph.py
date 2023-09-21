import pickle
from pathlib import Path

import networkx as nx
from networkx import MultiDiGraph
import numpy as np
# importing networkx
# importing matplotlib.pyplot
import matplotlib.pyplot as plt
# from ortools.graph.python import min_cost_flow
from examples.assignment_functions import _get_directed_graph, _create_layered_graph

root_folder = Path(
    r'C:\Users\asgarpou\OneDrive - Stichting Deltares\Documents\Projects\Short involvements\Moonshot5_hackathon\data\Moonshot_5')

# with open(root_folder / "generated" / "graph.p", 'rb') as handle:
#     graph = pickle.load(handle)

graph = nx.MultiGraph()
graph.add_node(1, demand=-2100, od_id="origin")
graph.add_node(4, demand=2100, od_id="destination")
graph.add_edge(1, 2, weight=3, capacity=10)
graph.add_edge(1, 3, weight=6, capacity=10)
graph.add_edge(2, 4, weight=1, capacity=40)
graph.add_edge(3, 4, weight=2, capacity=20)

directed_graph = _get_directed_graph(graph)

fig = plt.figure()
ax = fig.add_subplot(111)
edge_labels = dict([((n1, n2), attr['capacity'])
                    for n1, n2, attr in directed_graph.edges(data=True)])
pos = nx.spring_layout(directed_graph)
nx.draw(directed_graph, pos, with_labels=True, arrows=True, node_size=5, node_color='r', font_color='m')
nx.draw_networkx_edge_labels(
    directed_graph, pos,
    edge_labels=edge_labels,
    font_color='red'
)
plt.show()

multi_layer_graph = _create_layered_graph(directed_graph)

fig = plt.figure()
ax = fig.add_subplot(111)
edge_labels = dict([((n1, n2), attr['capacity'])
                    for n1, n2, attr in multi_layer_graph.edges(data=True)])
pos = nx.spring_layout(multi_layer_graph)
nx.draw(multi_layer_graph, pos, with_labels=True, arrows=True, node_size=5, node_color='r', font_color='m')
nx.draw_networkx_edge_labels(
    multi_layer_graph, pos, label_pos=0.4, edge_labels=edge_labels, font_color='red')
plt.show()

flow_dict = nx.min_cost_flow(multi_layer_graph)
a = 1
