# -*- coding: utf-8 -*-
"""
Created on 8-6-2022

@author: F.C. de Groen, Deltares
"""

import shutil

from ra2ce.ra2ce import main
from tests import test_data


class TestNetworkCreation:
    def test_1_network_shape(self):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data.
        test_name = "1_network_shape"
        _test_dir = test_data / test_name
        network_ini = _test_dir / "network.ini"
        assert network_ini.is_file()

        _output_graph_dir = _test_dir / "static" / "output_graph"
        if _output_graph_dir.is_dir():
            shutil.rmtree(_output_graph_dir)

        # 2. When run test.
        main(network_ini=network_ini)

        # 3. Then verify expectations.
        _expected_files = [
            "1_network_shape_lines_that_merged.shp",
            "base_graph.p",
            "base_network.feather",
        ]

        def validate_file(filename: str):
            _graph_file = _output_graph_dir / filename
            return _graph_file.is_file() and _graph_file.exists()

        assert all(map(validate_file, _expected_files))

    def test_3_network_osm_download(self):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data.
        test_name = "3_network_osm_download"
        _test_dir = test_data / test_name
        network_ini = _test_dir / "network.ini"
        assert network_ini.is_file()

        _output_graph_dir = _test_dir / "static" / "output_graph"
        if _output_graph_dir.is_dir():
            shutil.rmtree(_output_graph_dir)

        # 2. When run test.
        main(network_ini=network_ini)

        # 3. Then verify expectations.
        _expected_files = [
            "base_graph.p",
            "base_network.feather",
            "simple_to_complex.json",
            "complex_to_simple.json",
        ]

        def validate_file(filename: str):
            _graph_file = _output_graph_dir / filename
            return _graph_file.is_file() and _graph_file.exists()

        assert all(map(validate_file, _expected_files))
