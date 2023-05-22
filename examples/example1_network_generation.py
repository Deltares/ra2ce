from pathlib import Path
import geopandas as gpd
import folium
import webbrowser

# Just to make sonar-cloud stop complaining.
_network_ini_name = "network.ini"


def visualise_map():
    global root_dir
    layers = []
    file_path = root_dir / r'static\output_graph\base_graph.html'
    for i, entity_type in enumerate(["edges", "nodes"]):
        base_graph_entity_path = root_dir / rf'static\output_graph\base_graph_{entity_type}.gpkg'
        gdf = gpd.read_file(base_graph_entity_path)
        if i == 0:
            base_graph_map = gdf.explore()
            layers.append(base_graph_map)
        else:
            base_graph_map = gdf.explore(m=layers[i-1])
        base_graph_map.save(file_path)
    webbrowser.open(str(file_path))


if __name__ == "__main__":
    from ra2ce.ra2ce_handler import Ra2ceHandler

    root_dir = Path(r'C:\repos\ra2ce\examples\Project')

    network_ini = root_dir / _network_ini_name
    assert network_ini.is_file()

    # When run test.
    handler = Ra2ceHandler(network=network_ini, analysis=None)  # you can also input only the network_ini
    handler.configure()  # this will configure (create) the network and do the overlay of the hazard map with the
    # network if there is any
    visualise_map()  # Show the created maps.
