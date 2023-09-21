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
from examples.assignment_functions import _get_directed_graph, _create_layered_graph, draw_graph, _add_pos
from ra2ce.graph.exporters.multi_graph_network_exporter import MultiGraphNetworkExporter
import geopandas as gpd

root_folder = Path(r"C:\Users\groen_fe\OneDrive - Stichting Deltares\1_Projects\Moonshot_5\network_with_all_data_0_5_capacity.p")

with open(root_folder, 'rb') as handle:
    graph = pickle.load(handle)

edges_without_hazard = gpd.read_file(r"C:\Users\groen_fe\Downloads\od_analysis_with_hazard_edges.gpkg")
list_ids = edges_without_hazard["osmid"].to_list()

edges_remove = []
for e in graph.edges(data=True, keys=True):
    if str(e[-1]["osmid"]) not in list_ids:
        edges_remove.append((e[0], e[1], e[2]))
graph.remove_edges_from(edges_remove)

graph = _add_pos(graph)

# draw_graph(graph)
# graph = nx.MultiGraph()
# graph.add_node(1, demand=-2100, od_id="origin", geometry=shapely.geometry.Point((1, 2)))
# graph.add_node(4, demand=2100, od_id="destination", geometry=shapely.geometry.Point((10, 20)))
# graph.add_edge(1, 2, weight=3, capacity=10)
# graph.add_edge(1, 3, weight=6, capacity=10)
# graph.add_edge(2, 4, weight=1, capacity=40)
# graph.add_edge(3, 4, weight=2, capacity=20)

directed_graph = _get_directed_graph(graph)
# draw_graph(directed_graph)

multi_layer_graph = _create_layered_graph(directed_graph, weight='length')
# draw_graph(multi_layer_graph)

flow_dict = nx.min_cost_flow(multi_layer_graph)
a = 1

# for n in graph.nodes(data=True):
edges_done = []
for n in flow_dict.keys():
    to_nodes = flow_dict[n].keys()
    for to_node in to_nodes:
        ks = flow_dict[n][to_node].keys()
        for k in ks:
            if (n, to_node, k) in edges_done:
                continue
            flow = flow_dict[n][to_node][k]
            if isinstance(to_node, int):
                try:
                    directed_graph[n][to_node][k]["flow"] = flow
                except KeyError:
                    print("not found")
            if flow > 0:
                try:
                    if isinstance(to_node, str) and isinstance(n, int):
                        directed_graph.nodes[n]["flow"] = flow
                        to_node_int = int(to_node.split('_')[0])
                        if to_node_int == n:
                            directed_graph.nodes[n]["bottleneck"] = "yes"
                            directed_graph[n][to_node][k]["bottleneck"] = "yes"
                    elif isinstance(n, str) and isinstance(to_node, int):
                        n_int = int(n.split('_')[0])
                        directed_graph.nodes[n_int]["flow"] = flow
                        if n_int == n:
                            directed_graph.nodes[n_int]["bottleneck"] = "yes"
                            directed_graph[n_int][to_node][k]["bottleneck"] = "yes"
                    elif isinstance(n, str) and isinstance(to_node, str):
                        print("skip")
                    elif isinstance(n, int) and isinstance(to_node, int):
                        directed_graph.nodes[n]["bottleneck"] = "no"
                        directed_graph.nodes[n]["flow"] = flow
                        directed_graph[n][to_node][k]["bottleneck"] = "no"
                    else:
                        print("WEIRD")
                except KeyError:
                    print("skip")
                
                edges_done.append((n, to_node, k))


directed_graph.graph["crs"] = "EPSG:4326"
exporter = MultiGraphNetworkExporter(basename="network_results_with_all_data_0_5_capacity_HAZARD", export_types=["shp", "pickle"])
exporter.export_to_shp(output_dir=Path(r"c:\Users\groen_fe\OneDrive - Stichting Deltares\1_Projects\Moonshot_5"), export_data=directed_graph)
exporter.export_to_pickle(output_dir=Path(r"c:\Users\groen_fe\OneDrive - Stichting Deltares\1_Projects\Moonshot_5"), export_data=directed_graph)