# -*- coding: utf-8 -*-
"""
Created on 8-6-2022

@author: F.C. de Groen, Deltares
"""

from pathlib import Path
import pandas as pd
import pytest
from tests.test_ra2ce import get_paths, check_output_files


def test_1_network_shape():
    """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
    from ra2ce.ra2ce import main

    test_name = "1_network_shape"
    network_ini, ana_conf = get_paths(test_name)
    main(network_ini=network_ini)
    check_output_files(test_name, ['1_network_shape_lines_that_merged.shp', 'base_graph.gpickle', 'base_network.feather'])


def test_3_network_osm_download():
    """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
    from ra2ce.ra2ce import main

    test_name = "3_network_osm_download"
    network_ini, ana_conf = get_paths(test_name)
    main(network_ini=network_ini)
    check_output_files(test_name, ['base_graph.gpickle', 'base_network.feather', 'simple_to_complex.json', 'complex_to_simple.json'])
