from pathlib import Path
import geopandas as gpd
from ra2ce.ra2ce_handler import Ra2ceHandler # import the ra2cehandler to run ra2ce analyses


root_dir = Path(__file__).parent.parent / 'data'#specify the path to the folder holding the RA2CE folder and input data
print(root_dir)


_network_ini_name = "network.ini" #set the name for the network.ini
_analyses_ini_name = "analyses.ini" #set the name for the analyses.ini

network_ini = root_dir / _network_ini_name
analyses_ini = root_dir / _analyses_ini_name
assert network_ini.is_file() # check whether the network.ini file exists


handler = Ra2ceHandler(network=network_ini, analysis=None)
handler.configure()


hazard_output = root_dir / "static" / "output_graph" / "base_graph_hazard_edges.gpkg"
hazard_gdf = gpd.read_file(hazard_output, driver = "GPKG")
hazard_gdf.head()


hazard_gdf.explore(column="EV1_ma", cmap="Reds")