# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""

from pathlib import Path
import logging


def input_validation(config):
    """ Check if input properties are correct and exist"""

    # check if properties exist in settings.ini file
    check_headers = ['project', 'network']
    check_headers.extend([a for a in config.keys() if 'analysis' in a])

    for k in check_headers:
        if k not in config.keys():
            logging.error('Property [ {} ] is not configured. Add property [ {} ] to the settings.ini file. '.format(k, k))
            quit()

    # check if properties have correct input
    # TODO: Decide whether also the non-used properties must be checked or those are not checked
    # TODO: Decide how to check for multiple analyses (analysis1, analysis2, etc)
    check_answer = {'source': ['OSM PBF', 'OSM download', 'shapefile', 'gpickle'],
                    'polygon': ['link', 'none'],
                    'directed': ['true', 'false'],
                    'network_type': ['walk', 'bike', 'drive', 'drive_service', 'all'],
                    'road_types': ['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary',
                                   'secondary_link', 'tertiary', 'tertiary_link', 'none'],  # TODO: add the lower types as well
                    'origin_destination': ['link', 'none'],
                    'save_shp': ['true', 'false'],
                    'save_csv': ['true', 'false'],
                    'analysis': ['direct', 'single_link_redundancy', 'multi_link_redundancy', 'multi_link_origin_destination'],
                    'hazard_map': ['link', 'none']}
    input_dirs = {'polygon': 'static/network', 'hazard_map': 'static/hazard'}

    for key in config:
        # First check the headers.
        if key in check_headers:
            # Now check the parameters per configured item.
            for item in config[key]:
                if item in check_answer:
                    if ('link' in check_answer[item]) and (config[key][item] != 'none'):
                        # Check if the path is an absolute path or a file name that is placed in the right folder
                        config[key][item] = check_paths(config, key, item, input_dirs)
                        continue

                    if item == 'road_types':
                        for road_type in config[key][item].replace(' ', '').split(','):
                            if road_type not in check_answer['road_types']:
                                logging.error('Wrong road type is configured ({}), has to be one or multiple of: {}'.format(road_type, check_answer['road_types']))
                        continue

                    if config[key][item] not in check_answer[item]:
                        logging.error('Wrong input to property [ {} ], has to be one of: {}'.format(item, check_answer[item]))
                        quit()

    return config


def check_paths(config, key, item, input_dirs):
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
            else:
                list_paths.append(abs_path)
        else:
            list_paths.append(p)
    return list_paths
