import pickle
from pathlib import Path

from networkx import MultiDiGraph

from examples.assignment_functions import _get_directed_graph, _create_layered_graph

root_folder = Path(
    r'C:\Users\asgarpou\OneDrive - Stichting Deltares\Documents\Projects\Short involvements\Moonshot5_hackathon\data\Moonshot_5')

with open(root_folder / "generated" / "graph.p", 'rb') as handle:
    graph = pickle.load(handle)


directed_graph = _get_directed_graph(graph)
layered_graph = _create_layered_graph(directed_graph)






