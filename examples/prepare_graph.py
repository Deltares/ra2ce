import pickle
from pathlib import Path

import networkx as nx
from networkx import MultiDiGraph

from examples.assignment_functions import _get_directed_graph, _create_layered_graph

root_folder = Path(
    r'C:\Users\asgarpou\OneDrive - Stichting Deltares\Documents\Projects\Short involvements\Moonshot5_hackathon\data\Moonshot_5')

# with open(root_folder / "generated" / "graph.p", 'rb') as handle:
#     graph = pickle.load(handle)

graph = nx.MultiDiGraph()
graph.add_node(1, demand=31, od_id="origin")
graph.add_node(4, demand=-31, od_id="destination")
graph.add_edge(1, 2, cost=3, capacity=40)
graph.add_edge(1, 3, cost=6, capacity=10)
graph.add_edge(2, 4, cost=1, capacity=20)
graph.add_edge(3, 4, cost=2, capacity=5)

directed_graph = _get_directed_graph(graph)
multi_layer_graph = _create_layered_graph(directed_graph)
flow_dict = nx.min_cost_flow(multi_layer_graph)

a = 1






