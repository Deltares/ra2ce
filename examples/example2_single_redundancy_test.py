from pathlib import Path
import geopandas as gpd
import webbrowser

_analysis_ini_name = "analysis.ini"


def visualise_map(file_name, file_path, map_entities=None):
    global root_dir
    file_full_path = Path(str(file_path / file_name) + '.html')
    if map_entities is not None:
        layers = []
        for i, entity_type in enumerate(map_entities):
            base_graph_entity_path = Path(str(file_path / file_name) + f'_{entity_type}.gpkg')
            gdf = gpd.read_file(base_graph_entity_path)
            if i == 0:
                base_graph_map = gdf.explore()
                layers.append(base_graph_map)
            else:
                base_graph_map = gdf.explore(m=layers[i-1])
            base_graph_map.save(file_full_path)
    else:
        base_graph_path = Path(str(file_path / file_name) + '.gpkg')
        gdf = gpd.read_file(base_graph_path)
        base_graph_map = gdf.explore()
        base_graph_map.save(file_full_path)
    webbrowser.open(str(file_full_path))


if __name__ == "__main__":
    from ra2ce.ra2ce_handler import Ra2ceHandler

    example_num = 2
    root_dir = Path(rf'C:\repos\ra2ce\examples\example_{example_num}')

    analysis_ini = root_dir / _analysis_ini_name
    assert analysis_ini.is_file()

    # When run test.
    handler = Ra2ceHandler(network=None, analysis=analysis_ini)  # you can also input only the network_ini
    handler.configure()  # this will configure (create) the network and do the overlay of the hazard map with the
    # network if there is any
    handler.run_analysis()  # this will run the analysis

    # Show the created maps.
    map_file_path = root_dir / r'output\single_link_redundancy'
    visualise_map(file_name='single_link_redundancy_test_1', file_path=map_file_path)
    visualise_map(file_name='single_link_redundancy_test_2', file_path=map_file_path)

