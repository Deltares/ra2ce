import shutil
import subprocess
from pathlib import Path
from typing import Optional

import pytest

from ra2ce import main
from tests import slow_test, test_data

# Just to make sonar-cloud stop complaining.
_network_ini_name = "network.ini"
_analysis_ini_name = "analyses.ini"
_base_graph_p_filename = "base_graph.p"
_base_network_feather_filename = "base_network.feather"


def _run_from_cli(network_ini: Optional[Path], analysis_ini: Optional[Path]) -> None:

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
        except ImportError as exc_err:
            pytest.fail(f"It was not possible to import required packages {exc_err}")

    @slow_test
    @pytest.mark.parametrize(
        "project_name",
        [
            pytest.param("acceptance_test_data", id="Default test data."),
            pytest.param(
                "wpf_nepal",
                id="Nepal project",
                marks=pytest.mark.skip(reason="WPF Nepal test directory not presnt"),
            ),
        ],
    )
    def test_given_test_data_main_does_not_throw(self, project_name: str):
        """
        ToDo: is this test necessary? Would it not be better to frame it in direct / indirect ?
        """
        _test_dir = test_data / project_name
        _network = _test_dir / _network_ini_name
        _analysis = _test_dir / _analysis_ini_name

        assert _network.is_file()
        assert _analysis.is_file()

        _run_from_cli(_network, _analysis)


class TestIndirectAnalyses:
    def test_1_1_given_only_network_shape_redundancy(self):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data
        test_name = "1_1_network_shape_redundancy"
        _test_dir = test_data / test_name
        network_ini = _test_dir / _network_ini_name
        analysis_ini = _test_dir / _analysis_ini_name
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
        _run_from_cli(network_ini, analysis_ini)

        # 3. Then, validate expectations
        _expected_graph_files = [
            _base_graph_p_filename,
            _base_network_feather_filename,
        ]
        for _graph_file in _expected_graph_files:
            _graph_file = _output_graph_dir / _graph_file
            assert _graph_file.is_file() and _graph_file.exists()
        for _analysis_output in _expected_analysis_output_files:
            assert _analysis_output.is_file() and _analysis_output.exists()

        # Purge output
        shutil.rmtree(_output_graph_dir, ignore_errors=True)
        shutil.rmtree(_output_files_dir, ignore_errors=True)

    @slow_test
    def test_4_analyses_indirect(self):
        """To test all indirect analyses."""
        # 1. Given test data.
        test_name = "4_analyses_indirect"
        _test_data_dir = test_data / test_name
        network_ini = _test_data_dir / _network_ini_name
        analyses_ini = _test_data_dir / _analysis_ini_name
        _output_files_dir = _test_data_dir / "output"
        shutil.rmtree(_output_files_dir, ignore_errors=True)

        _expected_analysis_files = dict(
            single_link_redundancy=[
                "single_link_redundancy_test.csv",
                "single_link_redundancy_test.gpkg",
            ],
            optimal_route_origin_destination=[
                "optimal_origin_dest_test.csv",
                "optimal_origin_dest_test.gpkg",
            ],
            multi_link_redundancy=[
                "multi_link_redundancy_test.csv",
                "multi_link_redundancy_test.gpkg",
            ],
            multi_link_origin_destination=[
                "multilink_origin_dest_test.csv",
                "multilink_origin_dest_test.gpkg",
                "multilink_origin_dest_test_impact_summary.csv",
                "multilink_origin_dest_test_impact.csv",
            ],
            multi_link_origin_closest_destination=[
                "multilink_origin_closest_dest_test_destinations.gpkg",
                "multilink_origin_closest_dest_test_optimal_routes.csv",
                "multilink_origin_closest_dest_test_optimal_routes_with_hazard.gpkg",
                "multilink_origin_closest_dest_test_optimal_routes_without_hazard.gpkg",
                "multilink_origin_closest_dest_test_origins.gpkg",
                "multilink_origin_closest_dest_test_results.xlsx",
                "multilink_origin_closest_dest_test_destinations.csv",
                "multilink_origin_closest_dest_test_results_edges.gpkg",
                "multilink_origin_closest_dest_test_results_nodes.gpkg",
            ],
        )
        # 2. When run test:
        _run_from_cli(network_ini, analyses_ini)

        # 3. Then validate expectations:
        for analysis, files in _expected_analysis_files.items():

            def _verify_file(a_file: Path):
                analysis_file = _output_files_dir / analysis / a_file
                assert (
                    analysis_file.is_file() and analysis_file.exists()
                ), "File {} does not exist".format(analysis_file.resolve())

            for file in files:
                _verify_file(file)


class TestNetworkCreation:
    # @pytest.mark.skip(
    #     reason="TODO: Seems to be missing some files generated by other tests."
    # )
    @slow_test
    def test_1_network_shape(self):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data.
        test_name = "1_network_shape"
        _test_data_dir = test_data / test_name
        network_ini = _test_data_dir / _network_ini_name
        assert network_ini.is_file()

        _output_graph_dir = _test_data_dir / "static" / "output_graph"
        shutil.rmtree(_output_graph_dir, ignore_errors=True)

        # 2. When run test.
        _run_from_cli(network_ini, None)

        # 3. Then verify expectations.
        _expected_files = [
            _base_graph_p_filename,
            _base_network_feather_filename,
        ]

        def validate_file(filename: str):
            _graph_file = _output_graph_dir / filename
            return _graph_file.is_file() and _graph_file.exists()

        assert all(map(validate_file, _expected_files))

    @slow_test
    def test_2_network_shape(self):
        """To test the graph and network creation from a shapefile.
        Applies line segmentation for the network and merges lines and cuts lines at the intersections for the graph.
        """
        # 1. Given test data.
        test_name = "2_network_shape"
        _test_data_dir = test_data / test_name
        network_ini = _test_data_dir / _network_ini_name
        assert network_ini.is_file()

        _output_graph_dir = _test_data_dir / "static" / "output_graph"
        shutil.rmtree(_output_graph_dir, ignore_errors=True)

        # 2. When run test.
        _run_from_cli(network_ini, None)

        # 3. Then verify expectations.
        _expected_files = [
            _base_graph_p_filename,
            _base_network_feather_filename,
        ]

        def validate_file(filename: str):
            _graph_file = _output_graph_dir / filename
            return _graph_file.is_file() and _graph_file.exists()

        assert all(map(validate_file, _expected_files))

    @slow_test
    def test_3_network_osm_download(self):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data.
        test_name = "3_network_osm_download"
        _test_data_dir = test_data / test_name
        network_ini = _test_data_dir / _network_ini_name
        assert network_ini.is_file()

        _output_graph_dir = _test_data_dir / "static" / "output_graph"
        shutil.rmtree(_output_graph_dir, ignore_errors=True)

        # 2. When run test.
        _run_from_cli(network_ini, None)

        # 3. Then verify expectations.
        _expected_files = [
            _base_graph_p_filename,
            _base_network_feather_filename,
            "simple_to_complex.json",
            "complex_to_simple.json",
        ]

        def validate_file(filename: str):
            _graph_file = _output_graph_dir / filename
            return _graph_file.is_file() and _graph_file.exists()

        assert all(map(validate_file, _expected_files))
