"""Top-level package for Risk Assessment and Adaptation for Critical infrastructurE."""

__author__ = """Frederique de Groen, Kees van Ginkel, Margreet van Marle, Amine Aboufirass"""
__email__ = 'Margreet.vanMarle@deltares.nl'
__version__ = '0.1.0'

print('Started configuration of RA2CE from .ini file in folder:')

import os, sys, logging
from pathlib import Path

folder = Path(__file__).parents[0]
print(folder)

#In the same way, we can import the other packages
import ra2ce.analyses_direct
print('"ra2ce.analyses_direct" imported')


LOG_FILENAME = folder / 'log_ra2ce.log'

logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    filename=LOG_FILENAME,
                    level=logging.INFO)


