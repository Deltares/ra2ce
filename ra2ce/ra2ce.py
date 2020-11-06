"""Main module.
Connecting to creating a network and/or graph, the analysis and the visualisations (for later).
"""

# external modules
import os, sys
folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder)
os.chdir(os.path.dirname(folder))  # set working directory to top folder

import pandas as pd

# local modules
from utils import load_config, create_path
from create_network_from_shp import create_network_from_shapefile
from create_network_from_osm_dump import from_dump_tool_workflow
from create_network_from_polygon import get_graph_from_polygon
import analyses_indirect as indirect
import analyses_direct as direct

crs_ = 4326


def configure_user_input(cfg):
    """Configures the user input into a dictionary.
    """
    df = pd.read_excel(cfg["filenames"]["user_input"])
    # clean up dataframe: remove rows and columns that only contain nan values
    df.dropna(axis=1, how='all', inplace=True)
    input_dict = df.to_dict(orient='index')

    for theAnalysis in input_dict.keys():
        if 'hazard_data' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['hazard_data'] = [os.path.join(cfg["paths"]["hazard"], x) for x in
                                 input_dict[theAnalysis]['hazard_data'].replace(" ", "").split(',')]
            input_dict[theAnalysis]['hazard_attribute_name'] = [x.strip() for x in input_dict[theAnalysis]['hazard_attribute_name'].split(',')]
        if 'shp_input_data' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['shp_input_data'] = create_path(input_dict[theAnalysis]['shp_input_data'],
                                                                    cfg["paths"]["network_shp"], '.shp')
        if 'shp_for_diversion' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['shp_for_diversion'] = create_path(input_dict[theAnalysis]['shp_for_diversion'],
                                                                    cfg["paths"]["network_shp"], '.shp')
        if 'OSM_area_of_interest' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['OSM_area_of_interest'] = create_path(input_dict[theAnalysis]['OSM_area_of_interest'],
                                                                    cfg["paths"]["area_of_interest"], '.shp')
        if 'path_to_pbf' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['name_of_pbf'] = create_path(input_dict[theAnalysis]['name_of_pbf'],
                                                                    cfg["paths"]["OSM_dumps"], '.pbf')
        if 'origin_shp' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['origin_shp'] = create_path(input_dict[theAnalysis]['origin_shp'],
                                                                    cfg["paths"]["OSM_dumps"], '.pbf')
        if 'destination_shp' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['destination_shp'] = create_path(input_dict[theAnalysis]['destination_shp'],
                                                                 cfg["paths"]["OSM_dumps"], '.pbf')
    return input_dict


def create_network(inputDict):
    """Depending on the user input, a network/graph is created.
    """

    # Create the network from the network source
    if inputDict['network_source'] == 'Network based on shapefile':
        G, edge_gdf = create_network_from_shapefile(inputDict, crs_)
    elif inputDict['network_source'] == 'Network based on OSM dump':
        roadTypes = inputDict['road_types'].lower().replace(' ', '').split(',')
        G, edge_gdf = from_dump_tool_workflow(inputDict["name_of_pbf"], roadTypes)
    elif inputDict['network_source'] == 'Network based on OSM online':
        networkType = inputDict['network_type'].lower().replace(' ', '')  # decapitalize and remove all whitespaces
        roadTypes = inputDict['road_types'].lower().replace(',', '|')
        G, edge_gdf = get_graph_from_polygon(inputDict["area_of_interest"], networkType, roadTypes)
    else:
        Exception("Check your user_input.xlsx, the input under 'network_source' is not one of the given options.")

    # # TODO: only create the graph/gdf if that one is needed
    # if inputDict['analysis'] == 'Direct Damages':
    #     # only create gdf
    # elif inputDict['analysis'] == 'Redundancy-based criticality':
    #     # only create graph
    # elif inputDict['analysis'] == 'Both':
    #     # create gdf and graph

    return G, edge_gdf


def start_analysis(inputDict, G, network):
    """Depending on the user input, an analysis is executed.
    """
    if inputDict['analysis'] == 'Direct Damages':
        print("Script not yet connected")
    elif inputDict['analysis'] == 'Redundancy-based criticality':
        if inputDict['links_analysis'] == 'Single-link Disruption':
            indirect.single_link_alternative_routes(G, inputDict)
        elif inputDict['links_analysis'] == 'Multi-link Disruption (1): Calculate the disruption for all damaged roads':
            indirect.multi_link_alternative_routes(G, inputDict)
        elif inputDict['links_analysis'] == 'Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix':
            indirect.multi_link_od_matrix(G, inputDict)
        else:
            Exception("Check your user_input.xlsx, the input under 'links_analysis' is not one of the given options.")

    elif inputDict['analysis'] == 'Both':
        # TODO The direct analysis
        # ...
        # The indirect analysis
        if inputDict['links_analysis'] == 'Single-link Disruption':
            indirect.single_link_alternative_routes(G, inputDict)
        elif inputDict['links_analysis'] == 'Multi-link Disruption (1): Calculate the disruption for all damaged roads':
            indirect.multi_link_alternative_routes(G, inputDict)
        elif inputDict['links_analysis'] == 'Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix':
            indirect.multi_link_od_matrix(G, inputDict)
        else:
            Exception("Check your user_input.xlsx, the input under 'links_analysis' is not one of the given options.")


def main(argv):
    # argv should be True or False
    config = load_config(test=argv[0])  # get config file
    # configure excel user input in the right format
    input_dict = configure_user_input(config)

    for analysis in input_dict.keys():
        # create the network: a geodataframe and/or graph is created depending on the user input
        graph, edgeGdf = create_network(input_dict[analysis])
        start_analysis(input_dict[analysis], graph, edgeGdf)
        print("Finished run", input_dict[analysis]['analysis_name'])

    print("Done.")


if __name__ == '__main__':
    main(sys.argv[1:])  # reads from the 2nd argument, the first argument is calling the script itself: ra2ce.py test
