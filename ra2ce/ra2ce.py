"""Main module.
Connecting to creating a network and/or graph, the analysis and the visualisations (for later).
"""

# external modules
import os, sys
folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder)

import pandas as pd

# local modules
from utils import load_config
from create_network_from_shp import create_network_from_shapefile
import analyses_indirect as indir
from create_network_from_osm_dump import get_graph_from_polygon
# import from direct analyses file

crs_ = 4326


def configure_user_input():
    """Configures the user input into a dictionary.
    """
    df = pd.read_excel(load_config()["filenames"]["user_input_tests"])
    # clean up dataframe: remove rows and columns that only contain nan values
    df.dropna(axis=1, how='all', inplace=True)
    input_dict = df.to_dict(orient='index')

    # TODO: implement function to map all the right values in the dict to a list
    #  (the filenames and things that belong to those files)
    for analysis in input_dict.keys():
        if 'hazard_data' in input_dict[analysis]:
            input_dict[analysis]['hazard_data'] = [os.path.join(load_config()["paths"]["test_hazard"], x) for x in
                                 input_dict[analysis]['hazard_data'].replace(" ", "").split(',')]
            input_dict[analysis]['hazard_attribute_name'] = [x.strip() for x in input_dict[analysis]['hazard_attribute_name'].split(',')]

    return input_dict

def create_network(inputDict):
    """Depending on the user input, a network/graph is created.
    """

    # Create the network from the network source
    if inputDict['network_source'] == 'Network based on shapefile':
        graph, gdf = create_network_from_shapefile(inputDict, crs_)
    elif inputDict['network_source'] == 'Network based on OSM dump':
        print("Script not yet connected")
    elif inputDict['network_source'] == 'Network based on OSM online':
        areaOfInterest = os.path.join(load_config()["paths"]["area_of_interest"], inputDict['OSM_area_of_interest'] + '.shp')
        networkType = inputDict['network_type'].lower().replace(' ', '')  # decapitalize and remove all whitespaces
        roadTypes = inputDict['road_types'].lower().replace(',', '|')
        graph, gdf = get_graph_from_polygon(areaOfInterest, networkType, roadTypes)
    else:
        Exception("Check your user_input.xlsx, the input under 'network_source' is not one of the given options.")

    # # TODO: only create the graph/gdf if that one is needed
    # if inputDict['analysis'] == 'Direct Damages':
    #     # only create gdf
    # elif inputDict['analysis'] == 'Redundancy-based criticality':
    #     # only create graph
    # elif inputDict['analysis'] == 'Both':
    #     # create gdf and graph

    return graph, gdf


def start_analysis(inputDict, G, network):
    """Depending on the user input, an analysis is executed.
    """
    if inputDict['analysis'] == 'Direct Damages':
        print("Script not yet connected")
    elif inputDict['analysis'] == 'Redundancy-based criticality':
        if inputDict['links_analysis'] == 'Single-link Disruption':
            indir.single_link_alternative_routes(G, inputDict, crs_)
        elif inputDict['links_analysis'] == 'Multi-link Disruption (1): Calculate the disruption for all damaged roads':
            indir.multi_link_alternative_routes(G, inputDict, crs_)
        elif inputDict['links_analysis'] == 'Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix':
            indir.multi_link_od_matrix(G, inputDict, crs_)
        else:
            Exception("Check your user_input.xlsx, the input under 'links_analysis' is not one of the given options.")

    elif inputDict['analysis'] == 'Both':
        # TODO The direct analysis
        # ...
        # The indirect analysis
        if inputDict['links_analysis'] == 'Single-link Disruption':
            indir.single_link_alternative_routes(G, inputDict)
        elif inputDict['links_analysis'] == 'Multi-link Disruption (1): Calculate the disruption for all damaged roads':
            indir.multi_link_alternative_routes(G, inputDict)
        elif inputDict['links_analysis'] == 'Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix':
            indir.multi_link_od_matrix(G, inputDict)
        else:
            Exception("Check your user_input.xlsx, the input under 'links_analysis' is not one of the given options.")


if __name__ == '__main__':
    # configure excel user input in the right format
    input_dict = configure_user_input()

    for analysis in input_dict.keys():
        # create the network: a geodataframe and/or graph is created depending on the user input
        graph, gdf = create_network(input_dict[analysis])
        start_analysis(input_dict[analysis], graph, gdf)
        print("Finished run", input_dict[analysis]['analysis_name'])

    print("Done.")
