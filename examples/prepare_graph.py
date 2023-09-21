import pickle
from pathlib import Path

import networkx as nx
import shapely.geometry
from networkx import MultiDiGraph
import numpy as np
# importing networkx
# importing matplotlib.pyplot
import matplotlib.pyplot as plt
# from ortools.graph.python import min_cost_flow
from examples.assignment_functions import _get_directed_graph, _create_layered_graph, draw_graph

root_folder = Path(
    r'C:\Users\asgarpou\OneDrive - Stichting Deltares\Documents\Projects\Short involvements\Moonshot5_hackathon\data\Moonshot_5')

# with open(root_folder / "generated" / "graph.p", 'rb') as handle:
#     graph = pickle.load(handle)

graph = nx.MultiGraph()
graph.add_node(1, demand=-2100, od_id="origin", geometry=shapely.geometry.Point((1, 2)))
graph.add_node(4, demand=2100, od_id="destination", geometry=shapely.geometry.Point((10, 20)))
graph.add_edge(1, 2, weight=3, capacity=10)
graph.add_edge(1, 3, weight=6, capacity=10)
graph.add_edge(2, 4, weight=1, capacity=40)
graph.add_edge(3, 4, weight=2, capacity=20)

directed_graph = _get_directed_graph(graph)
draw_graph(directed_graph)

multi_layer_graph = _create_layered_graph(directed_graph)
draw_graph(multi_layer_graph)

flow_dict = nx.min_cost_flow(multi_layer_graph)
a = 1
