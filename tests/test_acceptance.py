import shutil
import subprocess
from itertools import chain
from pathlib import Path
from typing import Dict, Iterator, List, Optional

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

    @pytest.fixture(autouse=False)
    def case_data_dir(self, request: pytest.FixtureRequest) -> Iterator[Path]:
        _test_data_dir = test_data / request.param
        _output_files_dir = _test_data_dir / "output"
        _output_graph_dir = _test_data_dir / "static" / "output_graph"

        def purge_output_dirs():
            shutil.rmtree(_output_files_dir, ignore_errors=True)
            shutil.rmtree(_output_graph_dir, ignore_errors=True)

        purge_output_dirs()
        yield _test_data_dir
        purge_output_dirs()

    @slow_test
    @pytest.mark.parametrize(
        "case_data_dir",
        [
            pytest.param("acceptance_test_data", id="Default test data."),
            pytest.param(
                "wpf_nepal",
                id="Nepal project",
                marks=pytest.mark.skip(reason="WPF Nepal test directory not presnt"),
            ),
        ],
        indirect=["case_data_dir"],
    )
    def test_given_test_data_main_does_not_throw(self, case_data_dir: Path):
        """
        ToDo: is this test necessary? Would it not be better to frame it in direct / indirect ?
        """
        _network = case_data_dir / _network_ini_name
        _analysis = case_data_dir / _analysis_ini_name

        assert _network.is_file()
        assert _analysis.is_file()

        _run_from_cli(_network, _analysis)

    @slow_test
    @pytest.mark.parametrize(
        "case_data_dir, expected_files",
        [
            pytest.param(
                "1_network_shape",
                [_base_graph_p_filename, _base_network_feather_filename],
                id="Case 1. Network creation from shp file.",
            ),
            pytest.param(
                "2_network_shape",
                [_base_graph_p_filename, _base_network_feather_filename],
                id="Case 2. Merges lines and cuts lines at the intersections",
            ),
            pytest.param(
                "3_network_osm_download",
                [
                    _base_graph_p_filename,
                    _base_network_feather_filename,
                    "simple_to_complex.json",
                    "complex_to_simple.json",
                ],
                id="Case 3. OSM download",
            ),
        ],
        indirect=["case_data_dir"],
    )
    def test_network_creation(self, case_data_dir: Path, expected_files: List[str]):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data.
        _output_graph_dir = case_data_dir / "static" / "output_graph"
        network_ini = case_data_dir / _network_ini_name
        assert network_ini.is_file()

        # 2. When run test.
        _run_from_cli(network_ini, None)

        # 3. Then verify expectations.
        def validate_file(filename: str):
            _graph_file = _output_graph_dir / filename
            return _graph_file.is_file() and _graph_file.exists()

        assert all(map(validate_file, expected_files))

    @slow_test
    @pytest.mark.parametrize(
        "case_data_dir, expected_graph_files, expected_analysis_files",
        [
            pytest.param(
                "1_1_network_shape_redundancy",
                [
                    _base_graph_p_filename,
                    _base_network_feather_filename,
                ],
                dict(single_link_redundancy=["single_link_redundancy_test.csv"]),
                id="Case 1. Given only network shape redundancy.",
            ),
            pytest.param(
                "4_analyses_indirect",
                [],
                dict(
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
                ),
                id="Case 2. All indirect analyses",
            ),
        ],
        indirect=["case_data_dir"],
    )
    def test_indirect_analysis(
        self,
        case_data_dir: Path,
        expected_graph_files: List[str],
        expected_analysis_files: Dict[str, List[str]],
    ):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data
        network_ini = case_data_dir / _network_ini_name
        analysis_ini = case_data_dir / _analysis_ini_name
        assert network_ini.is_file()
        assert analysis_ini.is_file()

        _graph_dir = case_data_dir / "static" / "output_graph"
        _analysis_dir = case_data_dir / "output"

        # 2. When test:
        _run_from_cli(network_ini, analysis_ini)

        # 3. Then, validate expectations
        def _verify_file(filepath: Path) -> bool:
            return filepath.exists() and filepath.is_file()

        # Graph files
        assert all(_verify_file(_graph_dir / _f) for _f in expected_graph_files)

        # Analysis files
        assert all(
            list(
                chain(
                    *(
                        list(map(lambda x: _verify_file(_analysis_dir / k / x), v))
                        for k, v in expected_analysis_files.items()
                    )
                )
            )
        )
