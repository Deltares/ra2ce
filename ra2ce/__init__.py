"""Top-level package for Risk Assessment and Adaptation for Critical infrastructurE."""
import os, sys, logging
from pathlib import Path
import warnings

__author__ = """Frederique de Groen, Kees van Ginkel, Margreet van Marle, Amine Aboufirass"""
__email__ = 'Margreet.vanMarle@deltares.nl'
__version__ = '0.1.0'


#@author of this ini: Kees van Ginkel
print('Started configuration of RA2CE from .ini file')
folder = Path(__file__).parents[0]
print('RA2CE code is located in:', folder)
print('Functionality can be imported as follows: "import ra2ce.analyses_direct as direct" or "from ra2ce.analyses_direct import fetch_roads"')

#In the same way, we can import the other packages
#import ra2ce.analyses_direct
#print('"ra2ce.analyses_direct" imported')


#INIT LOGGING
LOG_FILENAME = folder / 'log_ra2ce.log'

logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filename=LOG_FILENAME,
                    level=logging.INFO)

print('Log file can be found in:',LOG_FILENAME)

#TELL USER ABOUT THE CONFIG FILE
config_path = Path(__file__).parents[1] / 'config.json'

if config_path.exists():
    print('RA2CE will use the default config file (not the test config), named config.json and located in the root folder')
    from ra2ce.utils import load_config
    config = load_config()
    if 'print_upon_init' in config:
        print(config['print_upon_init'])
else:
    warnings.warn('The config.json file is not present in the expected folder, namely: {}'.format(Path(__file__).parents[1]))


