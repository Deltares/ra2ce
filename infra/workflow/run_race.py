from pathlib import Path

import geopandas as gpd

from ra2ce.ra2ce_handler import (
    Ra2ceHandler,  # import the ra2cehandler to run ra2ce analyses
)

_network_ini_name = "network.ini"  # set the name for the network.ini settings file

folder_dir = Path(r"/data")

root_dir = folder_dir  # specify the path to the project folder in the examples folder
network_ini = (
    root_dir / _network_ini_name
)  # we set the _network_ini_name before, so we can use this now for the project
assert network_ini.is_file()  # check whether the network.ini file exists

handler = Ra2ceHandler(network_ini=network_ini, analysis_ini=None)
handler.configure()

# Set the path to your output_graph folder to find the network/graph creation:
path_output_graph = root_dir / "static" / "output_graph"

# Now we find and inspect the file 'base_graph_edges.gpkg' which holds the 'edges' of the network.
# An edge (or link) of a network (or graph) represents a connection between two nodes (or vertices) of the network. More information on: https://mathinsight.org/definition/network_edge#:~:text=An%20edge%20(or%20link)%20of,in%20the%20first%20figure%20below.
base_graph_edges = path_output_graph / "base_graph_edges.gpkg"
edges_gdf = gpd.read_file(base_graph_edges, driver="GPKG")
edges_gdf.head()

edges_gdf.explore(column="highway", tiles="CartoDB positron")
