"""Main module.
Connecting to creating a network and/or graph, the analysis and the visualisations (for later).
"""

# external modules
import os, sys
import networkx as nx
import pickle
import logging
import numpy as np


folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder)
os.chdir(os.path.dirname(folder))  # set working directory to top folder

import pandas as pd
from pathlib import Path

# local modules
from utils import load_config, create_path
from create_network_from_shp import create_network_from_shapefile
from create_network_from_osm_dump import from_dump_tool_workflow
from create_network_from_osm_dump import graph_to_gdf
from create_network_from_polygon import from_polygon_tool_workflow
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
        input_dict[theAnalysis]['output'] = cfg["paths"]["output"]
        if 'hazard_data' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['hazard_data'] = [os.path.join(cfg["paths"]["hazard"], x) for x in
                                 input_dict[theAnalysis]['hazard_data'].replace(" ", "").split(',')]
            input_dict[theAnalysis]['hazard_attribute_name'] = [x.strip() for x in input_dict[theAnalysis]['hazard_attribute_name'].split(',')]
        if 'hazard_pickle' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['hazard_pickle'] = Path(cfg["paths"]["hazard"] / input_dict[theAnalysis]['hazard_pickle'])
        if 'shp_input_data' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['shp_input_data'] = create_path(input_dict[theAnalysis]['shp_input_data'],
                                                                    cfg["paths"]["network_shp"], '.shp')
        if 'shp_for_diversion' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['shp_for_diversion'] = create_path(input_dict[theAnalysis]['shp_for_diversion'],
                                                                    cfg["paths"]["network_shp"], '.shp')
        if 'OSM_area_of_interest' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['OSM_area_of_interest'] = create_path(input_dict[theAnalysis]['OSM_area_of_interest'],
                                                                    cfg["paths"]["area_of_interest"], '.shp')
            input_dict[theAnalysis]['shp_unique_ID'] = 'G_simple_fid'
        if 'name_of_pbf' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['name_of_pbf'] = Path(cfg["paths"]["OSM_dumps"] / input_dict[theAnalysis]['name_of_pbf'])
        if 'origin_shp' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['o_names'] = input_dict[theAnalysis]['origin_shp']
            input_dict[theAnalysis]['origin_shp'] = create_path(input_dict[theAnalysis]['origin_shp'],
                                                                    cfg["paths"]["origin_destination"], '.shp')
        if 'destination_shp' in input_dict[theAnalysis]:
            input_dict[theAnalysis]['d_names'] = input_dict[theAnalysis]['destination_shp']
            input_dict[theAnalysis]['destination_shp'] = create_path(input_dict[theAnalysis]['destination_shp'],
                                                                 cfg["paths"]["origin_destination"], '.shp')

    return input_dict


def create_network(inputDict):
    """Depending on the user input, a network/graph is created.
    """
    output_path = inputDict['output']

    # when G_simple and edges_complex already exist no need to create new graph and gdf
    G_simple_path = Path(inputDict['output'] / (str(inputDict['analysis_name'])+'_G_simple.gpickle'))
    edges_complex_path = Path(inputDict['output'] / (str(inputDict['analysis_name'])+'_edges_complex.p'))

    #check whether the paths exist
    if not (G_simple_path.exists() and edges_complex_path.exists()):
        # Create the network from the network source
        if inputDict['network_source'] == 'Network based on shapefile':
            print('start creating network from shapefile')
            G, edge_gdf = create_network_from_shapefile(inputDict, crs_)
        elif inputDict['network_source'] == 'Network based on OSM dump':
            print('start creating network from osm_dump')
            roadTypes = inputDict['road_types'].lower().replace(' ', ' ').split(',')
            #todo: built in that save_shp is automatically None based on input table
            G, edge_gdf = from_dump_tool_workflow(inputDict, roadTypes, save_files=True, segmentation=None, save_shapes=inputDict["output"],simplify=True) #in case of save shapes add here path
        elif inputDict['network_source'] == 'Network based on OSM online':
            print('start creating network from osm_online')
            inputDict['network_type'] = inputDict['network_type'].lower().replace(' ',
                                                                                  '')  # decapitalize and remove all whitespaces
            if 'road_types' in inputDict:
                inputDict['road_types'] = inputDict['road_types'].lower().replace(', ', '|')
            G, edge_gdf = from_polygon_tool_workflow(inputDict,save_shapes=True,save_files=True)
        else:
            Exception("Check your user_input.xlsx, the input under 'network_source' is not one of the given options.")
    else:
        print('G_simple already exists, uses the existing one!: {}'.format(G_simple_path))
        print('edge_complex already exists, uses the existing one!: {}'.format(edges_complex_path))
        # CONVERT GRAPHS TO GEODATAFRAMES
        G = nx.read_gpickle(G_simple_path)
        with open(edges_complex_path, 'rb') as f:
            edge_gdf = pickle.load(f)




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
        #TODO DONE FOR RWS Project, should be removed in ra2ce.
        elif inputDict['links_analysis'] == 'Multi-link Disruption_RWS':
            costs = indirect.multi_link_alternative_routes_rws(G, inputDict)
            return costs
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

def main_rws(argv):
    # argv should be True or False
    config = load_config(test=argv[0])  # get config file
    # configure excel user input in the right format
    input_dict = configure_user_input(config)

    # create the network: a geodataframe and/or graph is created depending on the user input
    graph, edgeGdf = create_network(input_dict[0])
    #create empty DF for the output
    summary_costs = pd.DataFrame({'extra_time': [], 'detour_Euro_ET_Hr': [], 'detour_Euro_AS_Hr': [], 'TNO_ET_Euro_Hr': [], 'TNO_AS_Euro_Hr': []})

    for analysis in input_dict.keys():
        input_dict[analysis]['output'] = Path(input_dict[analysis]['output'] / input_dict[analysis]['hazard_unique_ID'])
        try:
            costs = start_analysis(input_dict[analysis], graph, edgeGdf)
            summary_costs=summary_costs.append(costs)
            summary_costs.to_pickle(input_dict[analysis]['output'] / 'summary_cost' / str('summary_costs_'+(str(input_dict[analysis]['analysis_name'])+'.p')))
            # summary_costs.to_csv(input_dict[analysis]['output'] / 'summary_cost' / 'summary_costs.csv')
            print("Finished run", input_dict[analysis]['analysis_name'])
        except:
            print("Calculation of indirect damages failed: {}".format(input_dict[analysis]['analysis_name']))
            costs = pd.Series({'extra_time': np.nan, 'detour_Euro_ET_Hr': np.nan,'detour_Euro_AS_Hr': np.nan,'TNO_ET_Euro_Hr': np.nan, 'TNO_AS_Euro_Hr': np.nan},name=str(input_dict[analysis]['analysis_name']))
            summary_costs=summary_costs.append(costs)
            # summary_costs.to_csv(input_dict[analysis]['output'] / 'summary_cost' / 'summary_costs.csv')
            summary_costs.to_pickle(input_dict[analysis]['output'] / 'summary_cost' / str('summary_costs_'+(str(input_dict[analysis]['analysis_name'])+'.p')))
            logging.info("Calculation of indirect damages failed: {}".format(input_dict[analysis]['analysis_name']))
            print("Finished run", input_dict[analysis]['analysis_name'])

    summary_costs.to_csv(input_dict[analysis]['output'] / 'summary_cost' / 'summary_costs.csv')


if __name__ == '__main__':

    # main(sys.argv[1:])  # reads from the 2nd argument, the first argument is calling the script itself: ra2ce.py test
    main('True')
    # main_rws('True')
    print('Done')



