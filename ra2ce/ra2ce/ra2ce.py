"""Main module.
Connecting to creating a network and/or graph, the analysis and the visualisations (for later).
"""

# local modules
from utils import load_config
from create_network_from_osm_dump import get_graph_from_polygon
from create_graph_shp import create_network_from_shapefile
# import from direct analyses file
# import from indirect analyses file


def configure_user_input(excelInputSheet):
    """Configures the user input into a dictionary.
    """


def create_network(inputDict):
    """Depending on the user input, a network/graph is created.
    """


def start_analysis(inputDict):
    """Depending on the user input, an analysis is executed.
    """


if __file__ == "__main__":
    # configure excel user input in the right format
    excel_input_sheet = "standard path to excel input sheet"
    input_dict = configure_user_input(excel_input_sheet)

    create_network(input_dict)
    start_analysis(input_dict)

    print("Finished run", input_dict['name'])
