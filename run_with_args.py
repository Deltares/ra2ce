# -*- coding: utf-8 -*-
"""
Created on 6-8-2021

@author: F.C. de Groen, Deltares
"""

import sys

from ra2ce.ra2ce import main

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        network_file = sys.argv[1]
        analyses_file = sys.argv[2]
        main(network_file , analyses_file)
