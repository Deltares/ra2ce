# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
@author: M. Kwant, Deltares
"""

from pathlib import Path
import logging

list_indirect_analyses = ['single_link_redundancy', 'multi_link_redundancy', 'optimal_route_origin_destination', 'multi_link_origin_destination']
list_direct_analyses = ['direct']


def input_validation(config):
    """ Check if input properties are correct and exist"""

    # check if properties exist in settings.ini file
    check_headers = ['project']
    check_headers.extend([a for a in config.keys() if 'analysis' in a])

    if 'network' in config.keys():
        check_shp_input(config['network'])
        check_headers.extend(['network', 'origins_destinations', 'hazard', 'cleanup'])

    for k in check_headers:
        if k not in config.keys():
            logging.error('Property [ {} ] is not configured. Add property [ {} ] to the settings.ini file. '.format(k, k))
            quit()

    # check if properties have correct input
    # TODO: Decide whether also the non-used properties must be checked or those are not checked
    # TODO: Decide how to check for multiple analyses (analysis1, analysis2, etc)
    list_analyses = list_direct_analyses + list_indirect_analyses
    check_answer = {'source': ['OSM PBF', 'OSM download', 'shapefile', 'pickle'],
                    'polygon': ['file', None],
                    'primary_file': ['file', None],
                    'diversion_file': ['file', None],
                    'directed': [True, False],
                    'network_type': ['walk', 'bike', 'drive', 'drive_service', 'all'],
                    'road_types': ['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary',
                                   'secondary_link', 'tertiary', 'tertiary_link', None],  # TODO: add the lower types as well
                    'origins': ['file', None],
                    'destinations': ['file', None],
                    'save_shp': [True, False],
                    'save_csv': [True, False],
                    'analysis': list_analyses,
                    'hazard_map': ['file', None],
                    'aggregate_wl': ['max', 'min', 'mean'],
                    'weighing': ['distance', 'time']}
    input_dirs = {'polygon': 'static/network', 'hazard_map': 'static/hazard', 'origins': 'static/network',
                  'destinations': 'static/network', 'primary_file': 'static/network', 'diversion_file': 'static/network'}

    error = False
    for key in config:
        # First check the headers.
        if key in check_headers:
            # Now check the parameters per configured item.
            for item in config[key]:
                if item in check_answer:
                    if ('file' in check_answer[item]) and (config[key][item] is not None):
                        # Check if the path is an absolute path or a file name that is placed in the right folder
                        config[key][item], error = check_paths(config, key, item, input_dirs, error)
                        continue

                    if item == 'road_types':
                        for road_type in config[key][item].replace(' ', '').split(','):
                            if road_type not in check_answer['road_types']:
                                logging.error('Wrong road type is configured ({}), has to be one or multiple of: {}'.format(road_type, check_answer['road_types']))
                                error = True
                        continue

                    if config[key][item] not in check_answer[item]:
                        logging.error('Wrong input to property [ {} ], has to be one of: {}'.format(item, check_answer[item]))
                        error = True

    # Quit if error
    if error:
        logging.error("There are inconsistencies in the settings.ini file. Please consult the log file for more information: {}".format(config['root_path'] / 'data' / config['project']['name'] / 'output' / 'RA2CE.log'))
        exit()

    return config


def check_paths(config, key, item, input_dirs, error):
    # Check if the path is an absolute path or a file name that is placed in the right folder
    list_paths = []
    for p in config[key][item].split(','):
        p = Path(p)
        if not p.is_file():
            abs_path = config['root_path'] / 'data' / config['project']['name'] / input_dirs[
                item] / p
            if not abs_path.is_file():
                logging.error(
                    'Wrong input to property [ {} ], file {} does not exist in folder {}'.format(
                        item, p,
                        config['root_path'] / 'data' / config['project']['name'] / input_dirs[
                            item]))
                error = True
            else:
                list_paths.append(abs_path)
        else:
            list_paths.append(p)
    return list_paths, error


def check_shp_input(config):
    """Checks if a file id is configured when using the option to create network from shapefile """
    if (config['source'] == 'shapefile') and (config['file_id'] is None):
        logging.error('Not possible to create network - Shapefile used as source, but no file_id configured in .ini file')
        quit()
