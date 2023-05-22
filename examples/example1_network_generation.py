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
    handler.run_analysis()  # this will run the analysis

    map_path = Path(r'C:\repos\ra2ce\examples\Project\static\network\map.geojson')
    gdf = gpd.read_file(mgit ap_path)
    gpd.explore(gdf)

