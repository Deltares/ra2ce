# -*- coding: utf-8 -*-
"""
Created on 8-6-2022

@author: F.C. de Groen, Deltares
"""

from pathlib import Path
import pandas as pd
import pytest
from tests.test_ra2ce import get_paths, check_output_files


@pytest.mark.skip(reason="work in progress")
def test_1_network_shape():
    """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
    from ra2ce.ra2ce import main

    network_ini, ana_conf = get_paths("1_network_shape")
    main(network_ini=network_ini)
    check_output_files(['1_network_shape_lines_that_merged.shp', 'base_graph.gpickle', 'base_network.feather'])


@pytest.mark.skip(reason="work in progress")
def test_output():
    """Sample pytest test function for output"""
    cases = ['direct', 'single_link_redundancy', 'multi_link_redundancy', 'optimal_route_origin_destination',
             'multi_link_origin_destination']
    input_network_path = Path('data/test/network.ini')
    input_analyses_path = Path('data/test/analyses.ini')
    ra2ce.main(input_network_path, input_analyses_path)

    # to_check = ['ra2ce_fid', 'alt_dist', 'alt_nodes', 'diff_dist']

    for case in cases:
        outputs_correct = lookup_output('data/test/output/correct', case)
        outputs_test = lookup_output('data/test/output', case)

        # Check if the pandas dataframes are equal in all aspects
        print(case)
        pd.testing.assert_frame_equal(outputs_test, outputs_correct)
