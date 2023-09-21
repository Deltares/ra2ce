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
graph.add_node(1, demand=-21, od_id="origin")
graph.add_node(4, demand=21, od_id="destination")
graph.add_edge(1, 2, weight=3, capacity=40)
graph.add_edge(1, 3, weight=6, capacity=10)
graph.add_edge(2, 4, weight=1, capacity=20)
graph.add_edge(3, 4, weight=2, capacity=5)

fig = plt.figure()
ax = fig.add_subplot(111)
ax.axis('off')
ax.axis('equal')
nx.draw(graph, with_labels=False, arrows=True, node_size=5, node_color='r', font_color='m')
plt.show()

directed_graph = _get_directed_graph(graph)
multi_layer_graph = _create_layered_graph(directed_graph)
flow_dict = nx.min_cost_flow(directed_graph)

a = 1






