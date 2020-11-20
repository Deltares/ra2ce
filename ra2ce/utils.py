import os
import json
from pathlib import Path


def load_config(test=False):
    """
    Read config.json
    NOTE: make sure your working directory is set to the highest level folder in the directory

    Arguments:
        *test* (Boolean) : Should the test config be used instead of the default config? (default False)

    Returns:
        *config* (dict) : Dict with structure:
            ['comment'] : 'String with info about the config"
            ['paths'] [key] : Pathlib path to folders
                      [another key]
            ['filenames'][key] : Pathlib path to files
            ['print_upon_init'] : (optionally) : text to print when RA2CE is initialised in use as a module
    @author: Kees van Ginkel
    """
    config_path = Path(__file__).parents[1] / 'config.json'
    if test:
        config_path = Path(__file__).parents[1] / 'test_config.json'
    with open(config_path, 'r') as config_fh:
        config = json.load(config_fh)

    #Convert to pathlib objects
    for key in ['paths','filenames']:
        for key2, value in config[key].items():
            config[key][key2] = Path(__file__).parents[1] / Path(value)
    return config

#TODO repalce os with path
def create_path(in_names, out_folder, extension):
    return [os.path.join(out_folder, x) if x.endswith('.shp') else os.path.join(out_folder, x + '.shp') for x in
        in_names.split(',')][0]  # todo: quick fix, look into this


if __name__=='__main__':
    print("Testing if the paths in the config file already exist")
    cfg = load_config()
    for key in cfg['paths']:
        path = cfg['paths'][key]
        print('{} : "{}"'.format(key, path))
        print(path.exists(), end="\n\n")

    print("This is a demo of how to use the load_config: ")
    demo_path = load_config()['paths']['network_shp']
    print(demo_path)
