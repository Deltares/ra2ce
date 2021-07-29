# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""

import logging
import networkx as nx
import osmnx
import numpy as np
from numpy import object as np_object
import geopandas as gpd


class IndirectAnalyses:
    def __init__(self, config, graph):
        self.config = config
        self.g = graph

    def single_link_redundancy(self):
        """
        This is the function to analyse roads with a single link disruption and
        an alternative route.

        Arguments:
            InputDict [dictionary] = dictionary of input data used for calculating
                the costs for taking alternative routes
            ParameterNamesDict [dictionary] = names of the parameters used for calculating
                the costs for taking alternative routes
        """

        # TODO adjust to the right names of the RA2CE tool
        # if 'road_usage_data_path' in InputDict:
        #     road_usage_data = pd.read_excel(InputDict['road_usage_data_path'])
        #     road_usage_data.dropna(axis=0, how='all', subset=['vehicle_type'], inplace=True)
        #     aadt_names = [aadt_name for aadt_name in road_usage_data['attribute_name'] if aadt_name == aadt_name]
        # else:
        #     aadt_names = None
        #     road_usage_data = pd.DataFrame()
        road_usage_data = None  # can be removed if the above is fixed
        aadt_names = None  # can be removed if the above is fixed

        # CALCULATE CRITICALITY
        # TODO return back to criticality_single_link. Now temporarily changed for RWS project

        # gdf = criticality_single_link_osm(G, InputDict['shp_unique_ID'], roadUsageData=road_usage_data, aadtNames=aadt_names)
        logging.info("Function [single_link_redundancy]: executing")
        gdf = self.criticality_single_link_osm()

        # Extra calculation possible (like multiplying the disruption time with the cost for disruption)
        # todo: input here this option

        logging.info("Full analysis [single_link_redundancy] finished.")
        return gdf

    def criticality_single_link_osm(self):
        """
        :param graph: graph on which to run analysis (MultiDiGraph)
        :return: df with dijkstra detour distance and path results
        """
        # TODO look at differences between this function and the criticality_single_link above and merge/remove one
        # create a geodataframe from the graph
        gdf = osmnx.graph_to_gdfs(self.g, nodes=False)

        # list for the length of the alternative routes
        alt_dist_list = []
        alt_nodes_list = []
        dif_dist_list = []
        for e_remove in list(self.g.edges.data(keys=True)):
            u, v, k, data = e_remove

            # if data['highway'] in attr_list:
            # remove the edge
            self.g.remove_edge(u, v, k)

            if nx.has_path(self.g, u, v):
                # calculate the alternative distance if that edge is unavailable
                alt_dist = nx.dijkstra_path_length(self.g, u, v, weight='length')
                alt_dist_list.append(alt_dist)

                # append alternative route nodes
                alt_nodes = nx.dijkstra_path(self.g, u, v)
                alt_nodes_list.append(alt_nodes)

                # calculate the difference in distance
                dif_dist_list.append(alt_dist - data['length'])
            else:
                alt_dist_list.append(np.NaN)
                alt_nodes_list.append(np.NaN)
                dif_dist_list.append(np.NaN)

            # add edge again to the graph
            self.g.add_edge(u, v, k, **data)

        # Add the new columns to the geodataframe
        gdf['alt_dist'] = alt_dist_list
        gdf['alt_nodes'] = alt_nodes_list
        gdf['diff_dist'] = dif_dist_list

        return gdf

    def multi_link_redundancy(self):
        print("multi_link_redundancy")
        return gpd.GeoDataFrame()

    def multi_link_origin_destination(self):
        return gpd.GeoDataFrame()

    def execute(self):
        """Executes the indirect analysis."""
        for analysis in self.config['indirect']:
            logging.info(f"----------------------------- Started analyzing '{analysis['name']}'  -----------------------------")
            if analysis['analysis'] == 'single_link_redundancy':
                gdf = self.single_link_redundancy()
            elif analysis['analysis'] == 'multi_link_redundancy':
                self.multi_link_redundancy()
            elif analysis['analysis'] == 'multi_link_origin_destination':
                self.multi_link_origin_destination()

            output_path = self.config['root_path'] / 'data' / self.config['project']['name'] / 'output' / analysis['analysis']
            output_path.mkdir(parents=True, exist_ok=True)
            if analysis['save_shp'] == 'true':
                shp_path = output_path / (analysis['name'].replace(' ', '_') + '.shp')
                save_gdf(gdf, shp_path)
            if analysis['save_csv'] == 'true':
                csv_path = output_path / (analysis['name'].replace(' ', '_') + '.csv')
                del gdf['geometry']
                gdf.to_csv(csv_path, index=False)

        return


def save_gdf(gdf, save_path):
    """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

    Arguments:
        gdf [geodataframe]: geodataframe object to be converted
        edge_shp [str]: output path including extension for edges shapefile
        node_shp [str]: output path including extension for nodes shapefile
    Returns:
        None
    """
    # save to shapefile
    gdf.crs = 'epsg:4326'  # TODO: decide if this should be variable with e.g. an output_crs configured

    for col in gdf.columns:
        if gdf[col].dtype == np_object and col != gdf.geometry.name:
            gdf[col] = gdf[col].astype(str)

    gdf.to_file(save_path, driver='ESRI Shapefile', encoding='utf-8')
    logging.info("Results saved to: {}".format(save_path))
