"""Top-level package for Risk Assessment and Adaptation for Critical infrastructurE."""

__author__ = """Margreet van Marle"""
__email__ = 'Margreet.vanMarle@deltares.nl'
__version__ = '0.1.0'

print('Started configuring RA2CE. This is awesome.')

import os, sys, logging
from pathlib import Path
folder = Path(__file__).parents[0]
print(folder)
#sys.path.append(folder)

#LOG_FILENAME = os.path.join(os.path.dirname(folder), './log_ra2ce.log')
LOG_FILENAME = folder / 'log_ra2ce.log'
if LOG_FILENAME.exists():
    print('er was er al eentje')
else: print('er was er geen')

logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filename=LOG_FILENAME,
                    level=logging.INFO)


