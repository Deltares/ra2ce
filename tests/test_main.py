import shutil
from itertools import chain
from pathlib import Path
from typing import Iterator, Optional

import pytest
from click.testing import CliRunner, Result

from ra2ce import __main__
from tests import external_test, slow_test, test_data, test_external_data

test_dir = test_data.joinpath("acceptance_test_data")

# Just to make sonar-cloud stop complaining.
_network_ini_name = "network.ini"
_analysis_ini_name = "analyses.ini"
_base_graph_p_filename = "base_graph.p"
_base_network_feather_filename = "base_network.feather"
_skip_cases = []


def get_external_test_cases() -> list[pytest.param]:
    if not test_external_data.exists():
        return []

    def get_pytest_param(test_dir: Path) -> pytest.param:
        _marks = [external_test]
        if test_dir.stem.lower() in _skip_cases:
            _marks.append(
                pytest.mark.skip(
                    reason=f"{test_dir.stem.capitalize()} not yet supported."
                )
            )
        return pytest.param(test_dir, id=test_dir.name.capitalize(), marks=_marks)

    return [
        get_pytest_param(_dir)
        for _dir in test_external_data.iterdir()
        if _dir.is_dir() and ".svn" not in _dir.name
    ]


_external_test_cases = get_external_test_cases()


class TestMainCli:
    def test_ra2ce_package_can_be_imported(self):
        """
        Import test. Not really necessary given the current way we are testing (directly to the cli). But better safe than sorry.
        """

        try:
            import ra2ce
            import ra2ce.__main__
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

    def _run_with_click(
        self, network_ini: Optional[Path], analysis_ini: Optional[Path]
    ) -> Result:
        args = []
        if network_ini:
            args.extend(["--network_ini", str(network_ini)])
        if analysis_ini:
            args.extend(["--analyses_ini", str(analysis_ini)])

        return CliRunner().invoke(
            __main__.run_analysis,
            args,
        )

    @pytest.mark.parametrize(
        "network_ini, analyses_ini, expected_error",
        [
            pytest.param(
                test_dir.joinpath("not_a_network.ini"),
                test_dir.joinpath("analyses.ini"),
                str(test_dir.joinpath("not_a_network.ini")),
                id="Network is None",
            ),
            pytest.param(
                test_dir.joinpath("network.ini"),
                test_dir.joinpath("not_an_analyses.ini"),
                str(test_dir.joinpath("not_an_analyses.ini")),
                id="Analyses is None",
            ),
        ],
    )
    def test_given_invalid_paths_raises_value_error(
        self, network_ini: Path, analyses_ini: Path, expected_error: str
    ):
        # 1 - 2. Define and run test data.
        _run_result = self._run_with_click(network_ini, analyses_ini)

        # 3. Verify expectations.
        assert _run_result.exit_code == 1
        assert FileNotFoundError == type(_run_result.exc_info[1])
        assert expected_error == str(_run_result.exc_info[1])

    @slow_test
    @pytest.mark.parametrize(
        "case_data_dir",
        [
            pytest.param("acceptance_test_data", id="Default test data"),
        ]
        + _external_test_cases,
        indirect=["case_data_dir"],
    )
    def test_given_test_data_main_does_not_throw(self, case_data_dir: Path):
        """
        ToDo: is this test necessary? Would it not be better to frame it in direct / indirect ?
        """
        # 1. Define test data.
        _network = case_data_dir.joinpath(_network_ini_name)
        _analysis = case_data_dir.joinpath(_analysis_ini_name)

        assert _network.is_file()
        assert _analysis.is_file()

        # 2. Run test.
        _run_result = self._run_with_click(_network, _analysis)

        # 3. Verify expectations.
        assert _run_result.exit_code == 0

    @pytest.mark.slow_test
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
                "4_analyses_losses",
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
                        "multilink_origin_closest_dest_test_destinations.csv",
                        "multilink_origin_closest_dest_test_destinations.gpkg",
                        "multilink_origin_closest_dest_test_optimal_routes.csv",
                        "multilink_origin_closest_dest_test_optimal_routes_with_hazard.gpkg",
                        "multilink_origin_closest_dest_test_optimal_routes_without_hazard.gpkg",
                        "multilink_origin_closest_dest_test_origins.gpkg",
                        "multilink_origin_closest_dest_test_results.xlsx",
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
        expected_graph_files: list[str],
        expected_analysis_files: dict[str, list[str]],
    ):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data
        network_ini = case_data_dir.joinpath(_network_ini_name)
        analysis_ini = case_data_dir.joinpath(_analysis_ini_name)
        assert network_ini.is_file()
        assert analysis_ini.is_file()

        _graph_dir = case_data_dir.joinpath("static", "output_graph")
        _analysis_dir = case_data_dir.joinpath("output")

        # 2. When test:
        _click_arguments = self._run_with_click(network_ini, analysis_ini)

        # 3. Then, validate expectations
        assert _click_arguments.exit_code == 0

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
