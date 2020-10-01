import os
import json

def load_config():
    """
    Read config.json
    NOTE: make sure your working directory is set to the highest level folder in the directory

    """
    config_path = os.path.join('test_config.json')
    with open(config_path, 'r') as config_fh:
        config = json.load(config_fh)
    return config

if __name__=='__main__':
    print("Testing if the paths in the config file already exist")
    config = load_config()
    for key in config['paths']:
        path = config['paths'][key]
        print('{} : "{}"'.format(key,path))
        print(os.path.exists(path),end="\n\n")

    print("This is a demo of how to use the load_config: ")
    demo_path = load_config()['paths']['test_network_shp']
    print(demo_path)
