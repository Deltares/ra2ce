import shutil
import subprocess
from pathlib import Path

import pytest

from ra2ce import main
from tests import test_data


def run_from_cli(network_ini: Path, analysis_ini: Path) -> None:

    assert Path(main.__file__).exists(), "No main file was found."

    args = [
        "python",
        main.__file__,
    ]
    if network_ini:
        args.extend(["--network_ini", str(network_ini)])
    if analysis_ini:
        args.extend(["--analyses_ini", str(analysis_ini)])

    _return_code = subprocess.call(args)
    assert _return_code == 0


class TestAcceptance:
    def test_ra2ce_package_can_be_imported(self):
        """
        Import test. Not really necessary given the current way we are testing (directly to the cli). But better safe than sorry.
        """

        try:
            import ra2ce
            import ra2ce.main
            import ra2ce.ra2ce_handler
        except ImportError:
            raise

    def test_given_test_data_main_does_not_throw(self):
        """
        ToDo: is this test necessary? Would it not be better to frame it in direct / indirect ?
        """
        _test_dir = test_data / "acceptance_test_data"
        _network = _test_dir / "network.ini"
        _analysis = _test_dir / "analyses.ini"

        assert _network.is_file()
        assert _analysis.is_file()

        run_from_cli(_network, _analysis)


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
        _output_files_dir = _test_dir / "output"

        shutil.rmtree(_output_graph_dir, ignore_errors=True)
        shutil.rmtree(_output_files_dir, ignore_errors=True)

        _expected_analysis_output_files = [
            _output_files_dir
            / "single_link_redundancy"
            / "single_link_redundancy_test.csv"
        ]

        # 2. When test:
        run_from_cli(network_ini, analysis_ini)

        # 3. Then, validate expectations
        _expected_graph_files = [
            "1_1_network_shape_redundancy_lines_that_merged.shp",
            "base_graph.p",
            "base_network.feather",
        ]
        for _graph_file in _expected_graph_files:
            _graph_file = _output_graph_dir / _graph_file
            assert _graph_file.is_file() and _graph_file.exists()
        for _analysis_output in _expected_analysis_output_files:
            assert _analysis_output.is_file() and _analysis_output.exists()

    @pytest.mark.skipif(
        reason="This test takes way too long due to the download of data."
    )
    def test_4_analyses_indirect(self):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data.
        test_name = "4_analyses_indirect"
        _test_data_dir = test_data / test_name
        network_ini = _test_data_dir / "network.ini"
        analyses_ini = _test_data_dir / "analyses.ini"
        _output_files_dir = _test_data_dir / "output"
        shutil.rmtree(_output_files_dir, ignore_errors=True)

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
        run_from_cli(network_ini, analyses_ini)

        # 3. Then validate expectations:
        for analysis, files in _expected_analysis_files.items():

            def _verify_file(a_file: Path):
                analysis_file = _output_files_dir / analysis / a_file
                return analysis_file.is_file() and analysis_file.exists()

            assert all(list(map(_verify_file, files)))


class TestNetworkCreation:
    @pytest.mark.skip(reason="Work in progress.")
    def test_1_network_shape(self):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data.
        test_name = "1_network_shape"
        _test_dir = test_data / test_name
        network_ini = _test_dir / "network.ini"
        assert network_ini.is_file()

        _output_graph_dir = _test_dir / "static" / "output_graph"
        shutil.rmtree(_output_graph_dir, ignore_errors=True)

        # 2. When run test.
        run_from_cli(network_ini, None)

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
        shutil.rmtree(_output_graph_dir, ignore_errors=True)

        # 2. When run test.
        run_from_cli(network_ini, None)

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
