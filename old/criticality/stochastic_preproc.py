# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 2019

@author: Frederique de Groen

This script is made for COACCH.

It prepares the graph of a country (and/or extra NUTS-3 regions) of choice to do a stochastic analysis.
"""

# import modules
import os
import pandas as pd
import networkx as nx
import pickle

# local modules
import network_functions as nf

## reload a module
import importlib
importlib.reload(nf)

# input
name = 'magna_streyr_factory_p2'
coacch_n_base = r'N:\Projects\11202000\11202067\F. Other information\Flooding and transport disruptions'
coacch_p_base = r'D:\netwerkanalyse'
tool_base = r'N:\Projects\11203500\11203770\B. Measurements and calculations\005 - criticality\tools'

osm_output = os.path.join(coacch_p_base, name)

data_floods = os.path.join(coacch_n_base, "EuropeFloodResults", "Model09_beta", "postproc", "baseline")
osm_data = os.path.join(coacch_n_base, "OSM_extracts", "europe_regions_pbf_VM")
osm_convert_path = os.path.join(coacch_p_base, "osmconvert64.exe")
osm_filter_path = os.path.join(coacch_p_base, "osmfilter.exe")
europe_osm_pbf = r"D:\COACCH_countries\europe.osm.pbf"
nuts_3_regions_path = r"D:\COACCH_countries\countries_shp\NUTS_RG_01M_2016_3035_LEVL_3.shp"
shp_path = r"D:\COACCH_countries\magna_streyr_factory_p2"
area_shp = r"D:\COACCH_countries\magna_streyr_factory_p2\magna_steyr_factory_p2.shp"
save_avg_speeds = os.path.join(coacch_n_base, "1_Time_Costs_and_Speed_Defs", "average_speed_osm_road_type_{}.csv".format(name))


aadt_path = None  # optional, if you have UNECE e-road data, point to this path (.xlsx), otherwise None
classify_eroads = False  # True ifq you want to classify the roads by e-road, otherwise false
crs = {'init': 'epsg:4326'}
# incl_nuts = ['ITH10', 'CH056', 'CH055', 'CH054', 'CH053', 'DE27A', 'DE21K', 'DE215', 'DE22A', 'DE222',
#              'CZ031', 'CZ064', 'SK010', 'SI031', 'SI032', 'DE27E', 'DE27B', 'DE21D', 'DE216', 'DE21F',
#              'DE21M', 'DE214', 'DE228', 'DE225', 'CZ063', 'SK021', 'HU221', 'HU222', 'SI033', 'SI034',
#              'SI041', 'SI042', 'ITH42', 'ITH33']  # list of NUTS-3 regions bordering Austria
incl_nuts3 = ['NL423', 'NL422', 'NL414', 'NL412', 'NL411', 'NL342', 'NL341', 'LU000', 'FRF32', 'FRF31',
             'FRF21', 'FRE21', 'FRE11', 'DEB24', 'DEB23', 'DEA2D', 'DEA28']  # list of NUTS-3 regions bordering Belgium
incl_countries = 'BE'  # 'AT' is austria - choose list of country codes or one country code
rp_choice = 100  # choose the return period

# initialise the variables
# 'length', 'alt_dist', 'dif_dist' <- names for distance measurement
# 'time', 'alt_time', 'dif_s' <-- names for time measurement
# list = [weighing_name, weighing, dif_name]
weighing = 'time'  # or distance
if weighing == 'distance':
    weighing_names = ['length', 'alt_dist', 'dif_dist']
elif weighing == 'time':
    weighing_names = ['time', 'alt_time', 'dif_s']

# import data from Kees' model
gdf_flood = nf.import_flood_data(data_floods, incl_nuts3, incl_countries, crs, save_shp=False)

# make integers from the flood data osm_id colomn
gdf_flood['osm_id'] = pd.to_numeric(gdf_flood['osm_id'])

# create a list of all AoI id numbers and save to a pickle for the stochastic analysis
all_aois_in_area = list(gdf_flood.loc[(gdf_flood['NUTS-0'] == incl_countries) &
                                      (gdf_flood['AoI_rp{}'.format(rp_choice)].notnull()),
                                      'AoI_rp{}'.format(rp_choice)].unique())
pickle.dump(all_aois_in_area, open(os.path.join(coacch_n_base, "2_Output_analyses_Network", "aois_{}.p".format(name)), 'wb'))

if classify_eroads:
    # Fetch e-roads data with OSM id
    dict_eroads = nf.fetch_e_roads_data(osm_data, incl_nuts3, incl_countries)
else:
    dict_eroads = None

# get poly file of country/NUTS-3 regions of choice
nf.poly_files_europe(os.path.join(osm_output, name + '.poly'), area_shp)
nf.clip_osm(osm_convert_path, europe_osm_pbf, os.path.join(osm_output, name + '.poly'), os.path.join(osm_output, name + '.o5m'))
nf.filter_osm(osm_filter_path, os.path.join(osm_output, name + '.o5m'), os.path.join(osm_output, name + '_till_secondary.o5m'))

# create a graph
G_original = nf.graph_from_osm(os.path.join(osm_output, name + '_till_secondary.o5m'), multidirectional=False)

# match flood data with road network and possibly e-roads
# match for each road segment the intersecting floods
G = nf.match_ids(G_original, gdf_flood, value_column="val_rp{}".format(rp_choice), group_column="AoI_rp{}".format(rp_choice), dict_eroads=dict_eroads, aadt_path=aadt_path)

# add other variables: time
# Define and assign average speeds; or take the average speed from an existing CSV
avg_speeds = nf.calc_avg_speed(G, 'highway', save_csv=True, save_path=save_avg_speeds)
avg_speeds = pd.read_csv(save_avg_speeds)
G = nf.assign_avg_speed(G, avg_speeds, 'highway')

# make a time value of seconds, length of road streches is in meters
for u, v, k, edata in G.edges.data(keys=True):
    hours = (edata['length'] / 1000) / edata['avgspeed']
    G[u][v][k][weighing] = hours * 3600

# Define O/D pairs; or take the OD pairs from an existing shapefile
centroids = nf.create_OD_pairs(nuts_3_regions_path, ['BE'], G, name=name, file_output=shp_path, save_shp=True, save_pickle=True)
# centroids = pickle.load(open(os.path.join(shp_path, "{}_OD.p".format(name)), 'rb'))
G = nf.add_centroid_nodes(G, centroids)

# calculate the preferred quickest route
pref_routes = nf.preferred_routes(G, weighing_name=weighing, name='time',
                                  file_output=r"P:\osm_flood\network_analysis\sweden",
                                  save_shp=True,
                                  save_pickle=True)

# save the graph
nx.write_gpickle(G, os.path.join(osm_output, '{}_graph.gpickle'.format(name)))
nf.graph_to_shp(G, os.path.join(shp_path, '{}_edges.shp'.format(name)), os.path.join(shp_path, '{}_nodes.shp'.format(name)))

# load the graph
G = nx.read_gpickle(os.path.join(osm_output, '{}_graph.gpickle'.format(name)))
