import os
import json


def load_config(test=False):
    """
    Read config.json
    NOTE: make sure your working directory is set to the highest level folder in the directory

    """
    config_path = './config.json'
    if test:
        config_path = './test_config.json'
    with open(config_path, 'r') as config_fh:
        config = json.load(config_fh)
    return config


def create_path(in_names, out_folder, extension):
    return [os.path.join(out_folder, x) if x.endswith('.shp') else os.path.join(out_folder, x + '.shp') for x in
        in_names.split(',')]


if __name__=='__main__':
    print("Testing if the paths in the config file already exist")
    cfg = load_config()
    for key in cfg['paths']:
        path = cfg['paths'][key]
        print('{} : "{}"'.format(key, path))
        print(os.path.exists(path), end="\n\n")

    print("This is a demo of how to use the load_config: ")
    demo_path = load_config()['paths']['network_shp']
    print(demo_path)
