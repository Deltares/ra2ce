from pathlib import Path
import geopandas as gpd

# Just to make sonar-cloud stop complaining.
_network_ini_name = "network.ini"

if __name__ == "__main__":
    from ra2ce.ra2ce_handler import Ra2ceHandler

    root_dir = Path(r'C:\repos\ra2ce\examples\Project')

    network_ini = root_dir / _network_ini_name
    assert network_ini.is_file()

    # 2. When run test.
    handler = Ra2ceHandler(network=network_ini, analysis=None)  # you can also input only the network_ini
    handler.configure()  # this will configure (create) the network and do the overlay of the hazard map with the
    # network if there is any

    base_graph_path = root_dir / r'static\output_graph\base_graph_edges.gpkg'
    gdf = gpd.read_file(base_graph_path)
    gpd.explore(gdf)

