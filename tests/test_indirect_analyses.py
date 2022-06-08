# -*- coding: utf-8 -*-
"""
Created on 8-6-2022

@author: F.C. de Groen, Deltares
"""

from tests.test_ra2ce import get_paths, check_output_files


def test_1_1_network_shape_redundancy():
    """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
    from ra2ce.ra2ce import main

    test_name = "1_1_network_shape_redundancy"
    network_ini, analyses_ini = get_paths(test_name)
    main(network_ini=network_ini, analyses_ini=analyses_ini)
    check_output_files(test_name, ['1_1_network_shape_redundancy_lines_that_merged.shp', 'base_graph.gpickle', 'base_network.feather'])

