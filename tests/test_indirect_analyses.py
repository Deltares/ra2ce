# -*- coding: utf-8 -*-
"""
Created on 8-6-2022

@author: F.C. de Groen, Deltares
"""

from tests.test_ra2ce import get_paths, check_output_files, check_output_graph_files


def test_1_1_network_shape_redundancy():
    """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
    from ra2ce.ra2ce import main

    test_name = "1_1_network_shape_redundancy"
    network_ini, analyses_ini = get_paths(test_name)
    main(network_ini=network_ini, analyses_ini=analyses_ini)
    check_output_graph_files(test_name, ['1_1_network_shape_redundancy_lines_that_merged.shp', 'base_graph.gpickle', 'base_network.feather'])
    check_output_files(test_name, 'single_link_redundancy', ['single_link_redundancy_test.csv'])


def test_4_analyses_indirect():
    """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
    from ra2ce.ra2ce import main

    test_name = "4_analyses_indirect"
    network_ini, analyses_ini = get_paths(test_name)
    main(network_ini=network_ini, analyses_ini=analyses_ini)
    check_output_files(test_name, 'single_link_redundancy',
                       ['single_link_redundancy_test.csv', 'single_link_redundancy_test.shp'])
    check_output_files(test_name, 'optimal_route_origin_destination',
                       ['optimal_origin_dest_test.csv', 'optimal_origin_dest_test.shp'])
    check_output_files(test_name, 'multi_link_redundancy',
                       ['multi_link_redundancy_test.csv', 'multi_link_redundancy_test.shp'])
    check_output_files(test_name, 'multi_link_origin_destination',
                       ['multilink_origin_dest_test.csv', 'multilink_origin_dest_test.shp',
                        'multilink_origin_dest_test_impact_summary.csv', 'multilink_origin_dest_test_impact.csv'])
    check_output_files(test_name, 'multi_link_origin_closest_destination',
                       ['multilink_origin_closest_dest_test_destinations.shp', 'multilink_origin_closest_dest_test_optimal_routes.csv',
                        'multilink_origin_closest_dest_test_optimal_routes.shp', 'multilink_origin_closest_dest_test_origins.shp',
                        'multilink_origin_closest_dest_test_results.xlsx', 'multilink_origin_closest_dest_test_destinations.csv',
                        'multilink_origin_closest_dest_test_results_edges.shp', 'multilink_origin_closest_dest_test_results_nodes.shp'])