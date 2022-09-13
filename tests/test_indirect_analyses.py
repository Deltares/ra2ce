# -*- coding: utf-8 -*-
import pathlib
import shutil

from ra2ce.ra2ce import main
from tests import test_data


class TestIndirectAnalyses:
    def test_1_1_given_only_network_shape_redundancy(self):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data
        test_name = "1_1_network_shape_redundancy"
        _test_dir = test_data / test_name
        network_ini = _test_dir / "network.ini"
        analysis_ini = _test_dir / "analyses.ini"
        assert network_ini.is_file()
        assert analysis_ini.is_file()
        # Purge output dirs.
        _output_graph_dir = _test_dir / "static" / "output_graph"
        if _output_graph_dir.is_dir():
            shutil.rmtree(_output_graph_dir)
        _output_files_dir = _test_dir / "output"
        if _output_files_dir.is_dir():
            shutil.rmtree(_output_files_dir)

        _expected_graph_files = [
            _output_graph_dir / "1_1_network_shape_redundancy_lines_that_merged.shp",
            _output_graph_dir / "base_graph.p",
            _output_graph_dir / "base_network.feather",
        ]
        _expected_analysis_output_files = [
            _output_files_dir
            / "single_link_redundancy"
            / "single_link_redundancy_test.csv"
        ]

        # 2. When test:
        main(network_ini=network_ini, analyses_ini=analysis_ini)

        # 3. Then, validate expectations
        for _graph_file in _expected_graph_files:
            assert _graph_file.is_file() and _graph_file.exists()
        for _analysis_output in _expected_analysis_output_files:
            assert _analysis_output.is_file() and _analysis_output.exists()

    def test_4_analyses_indirect(self):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data.
        test_name = "4_analyses_indirect"
        _test_data_dir = test_data / test_name
        network_ini = _test_data_dir / "network.ini"
        analyses_ini = _test_data_dir / "analyses.ini"
        _output_files_dir = _test_data_dir / "static" / "output_graph"
        _expected_analysis_files = dict(
            single_link_redundancy=[
                "single_link_redundancy_test.csv",
                "single_link_redundancy_test.shp",
            ],
            optimal_route_origin_destination=[
                "optimal_origin_dest_test.csv",
                "optimal_origin_dest_test.shp",
            ],
            multi_link_redundancy=[
                "multi_link_redundancy_test.csv",
                "multi_link_redundancy_test.shp",
            ],
            multi_link_origin_destination=[
                "multilink_origin_dest_test.csv",
                "multilink_origin_dest_test.shp",
                "multilink_origin_dest_test_impact_summary.csv",
                "multilink_origin_dest_test_impact.csv",
            ],
            multi_link_origin_closest_destination=[
                "multilink_origin_closest_dest_test_destinations.shp",
                "multilink_origin_closest_dest_test_optimal_routes.csv",
                "multilink_origin_closest_dest_test_optimal_routes.shp",
                "multilink_origin_closest_dest_test_origins.shp",
                "multilink_origin_closest_dest_test_results.xlsx",
                "multilink_origin_closest_dest_test_destinations.csv",
                "multilink_origin_closest_dest_test_results_edges.shp",
                "multilink_origin_closest_dest_test_results_nodes.shp",
            ],
        )
        # 2. When run test:
        main(network_ini=network_ini, analyses_ini=analyses_ini)

        # 3. Then validate expectations:
        for analysis, files in _expected_analysis_files.items():

            def _verify_file(a_file: pathlib.Path):
                analysis_file = _output_files_dir / analysis / a_file
                return analysis_file.is_file() and analysis_file.exists()

            assert all(map(_verify_file, files))
