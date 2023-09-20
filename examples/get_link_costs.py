from pathlib import Path

from networkx import MultiGraph

from ra2ce.common.io.readers import GraphPickleReader

root_folder = Path(r'C:\Users\asgarpou\OneDrive - Stichting Deltares\Documents\Projects\Short involvements\Moonshot5_hackathon\data\Moonshot_5')
folder_dir = root_folder / r'test_graph_od'
od_graph = folder_dir / "static" / "output_graph" / "origins_destinations_graph.p"
graph = GraphPickleReader().read(od_graph)

cost_function = 'free_flow_time'

for edge in graph.edges(data=True):
    edge_attr = edge[2]
    if cost_function == 'free_flow_time':
        edge_attr['cost'] = edge_attr['length']/(edge_attr['avgspeed']*1000)
    elif cost_function == 'ff_time_emission':
        pass
    else:
        raise NotImplementedError('Cost function is not implemented yet')


class CostFunction:
    cost_funtion_name: str
    graph: MultiGraph
    