import pickle
from pathlib import Path

from networkx import MultiGraph

from ra2ce.common.io.readers import GraphPickleReader

root_folder = Path(
    r'C:\Users\asgarpou\OneDrive - Stichting Deltares\Documents\Projects\Short involvements\Moonshot5_hackathon\data\Moonshot_5')
pickled_graph = root_folder / "input" / "updated_network.p"
graph = GraphPickleReader().read(pickled_graph)

# cost_function = 'free_flow_time'
cost_function = 'distance'

for edge in graph.edges(data=True):
    edge_attr = edge[2]
    if cost_function == 'free_flow_time':
        edge_attr['cost'] = edge_attr['length'] / (edge_attr['avgspeed'] * 1000)
    elif cost_function == 'distance':
        edge_attr['cost'] = edge_attr['length']
    else:
        raise NotImplementedError('Cost function is not implemented yet')

with open(root_folder / "generated" / "graph.p", 'wb') as handle:
    pickle.dump(graph, handle, protocol=pickle.HIGHEST_PROTOCOL)
a = 1
