# -*- coding: utf-8 -*-
"""
Created on 26-7-2021

@author: F.C. de Groen, Deltares
"""

from pathlib import Path

# Local modules
from utils import parse_config
from checks import input_validation
from graph.networks import Network
from analyses.direct import analyses_direct
from analyses.indirect import analyses_indirect


def main():
    # Find the settings.ini file
    root_path = Path(r'd:\ra2ceMaster\ra2ce')
    setting_file = root_path / 'settings.ini'

    config = parse_config(path=setting_file)
    input_validation(config)
    network = Network(config)
    network.network_osm_download()
    # analysis()


if __name__ == '__main__':
    main()
