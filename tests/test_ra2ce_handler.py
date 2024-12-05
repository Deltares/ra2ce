import shutil
from pathlib import Path
from typing import Iterator

import pytest
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionBase,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import (
    AnalysisConfigDataReader,
)
from ra2ce.analysis.analysis_result.analysis_result_wrapper_.protocol import (
    AnalysisResultWrapperProtocol,
)
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_config_data.network_config_data_reader import (
    NetworkConfigDataReader,
)
from ra2ce.ra2ce_handler import Ra2ceHandler
from tests import test_data, test_results


class TestRa2ceHandler:
    def test_initialize_with_no_network_nor_analysis_does_not_raise(self):
        # 1. Run test.
        _handler = Ra2ceHandler(None, None)

        # 2. Verify final expectations.
        assert isinstance(_handler, Ra2ceHandler)

    @pytest.mark.parametrize(
        "analysis_config_data",
        [
            pytest.param(None, id="No analysis config"),
            pytest.param(AnalysisConfigData(), id="Empty analysis config"),
        ],
    )
    @pytest.mark.parametrize(
        "network_config_data",
        [
            pytest.param(None, id="No network config"),
            pytest.param(NetworkConfigData(), id="Empty network config"),
        ],
    )
    def test_initialize_from_valid_config_does_not_raise(
        self,
        network_config_data: NetworkConfigData,
        analysis_config_data: AnalysisConfigData,
    ):
        # 1./2. Define test data/Run test.
        _handler = Ra2ceHandler.from_config(network_config_data, analysis_config_data)

        # 3. Verify expectations.
        assert isinstance(_handler, Ra2ceHandler)

    @pytest.fixture(name="minimal_acceptance_test_case")
    def _get_acceptance_test_data_copy_dir(
        self, request: pytest.FixtureRequest
    ) -> Iterator[Path]:
        _reference_dir = test_data.joinpath("simple_inputs")
        assert _reference_dir.exists()

        # Define the results directory for this test case.
        _test_case_dir = test_results.joinpath(request.node.originalname)
        if request.node.originalname != request.node.name:
            _test_case_dir = _test_case_dir.joinpath(
                request.node.name.split("[")[-1].split("]")[0].lower().replace(" ", "_")
            )

        # This ensures we handle both unparametrized and parametrized tests.
        if _test_case_dir.exists():
            shutil.rmtree(_test_case_dir)
        _test_case_dir.parent.mkdir(exist_ok=True)

        shutil.copytree(_reference_dir, _test_case_dir)
        yield _test_case_dir

    @pytest.fixture(name="simple_test_case_files")
    def _get_simple_test_case_files(
        self, minimal_acceptance_test_case: Path
    ) -> Iterator[tuple[Path, Path]]:
        _network_file = minimal_acceptance_test_case.joinpath("network.ini")
        assert _network_file.exists()

        _analyses_file = minimal_acceptance_test_case.joinpath("analysis.ini")
        assert _analyses_file.exists()

        yield (_network_file, _analyses_file)

    @pytest.fixture(name="simple_test_case_configs")
    def _get_simple_test_case_configs(
        self, simple_test_case_files: tuple[Path, Path], request: pytest.FixtureRequest
    ) -> Iterator[tuple[NetworkConfigData, AnalysisConfigData]]:
        # Network config data.
        _network_config_data = NetworkConfigDataReader().read(simple_test_case_files[0])
        _network_config_data.input_path = simple_test_case_files
        assert isinstance(_network_config_data, NetworkConfigData)

        # Analysis config data
        _analysis_config_data = AnalysisConfigDataReader().read(
            simple_test_case_files[1]
        )
        assert isinstance(_analysis_config_data, AnalysisConfigData)

        if request.param_index != 0:
            _return_network, _return_analysis = request.param
            if _return_network is False:
                _network_config_data = None
            if _return_analysis is False:
                _analysis_config_data = None

        yield (_network_config_data, _analysis_config_data)

    @pytest.mark.slow_test
    @pytest.mark.parametrize(
        "simple_test_case_configs",
        [
            pytest.param((False, False), id="No config data provided"),
            pytest.param((False, True), id="Only network config data provided"),
            pytest.param((True, False), id="Only analysis config data provided"),
            pytest.param((True, True), id="All config data provided"),
        ],
        indirect=True,
    )
    def test_configure_handler_created_from_config_does_not_raise(
        self, simple_test_case_configs: tuple[NetworkConfigData, AnalysisConfigData]
    ):
        # 1./2. Define test data./Run test.
        _handler = Ra2ceHandler.from_config(
            simple_test_case_configs[0], simple_test_case_configs[1]
        )
        _handler.configure()

        # 3. Verify expectations.
        assert isinstance(_handler, Ra2ceHandler)

    def test_initialize_without_analysis_raises(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _test_dir = test_results.joinpath(request.node.name)
        _analysis_dir = _test_dir.joinpath("analysis_folder")
        if _test_dir.exists():
            shutil.rmtree(_test_dir)
        assert not _analysis_dir.exists()

        # 2. Run test.
        with pytest.raises(Exception):
            Ra2ceHandler(None, _analysis_dir)

        # 3. Verify expectations.
        assert _test_dir.exists()
        assert _test_dir.joinpath("output").exists()

    def _validate_run_results_with_simple_test_case(
        self, results: list[AnalysisResultWrapperProtocol]
    ):
        assert len(results) == 1
        _found_result = results[0]
        assert isinstance(_found_result, AnalysisResultWrapperProtocol)
        assert _found_result.is_valid_result()

        assert any(_found_result.results_collection)
        for _ra in _found_result.results_collection:
            assert isinstance(_ra.analysis_result, GeoDataFrame)
            assert isinstance(_ra.analysis_config, AnalysisSectionBase)
            assert isinstance(_ra.output_path, Path)

    @pytest.mark.slow_test
    def test_run_with_ini_files_given_valid_files(
        self, simple_test_case_files: tuple[Path, Path]
    ):
        # 1. Run test.
        _results = Ra2ceHandler.run_with_ini_files(
            simple_test_case_files[0], simple_test_case_files[1]
        )

        # 2. Verify expectations.
        self._validate_run_results_with_simple_test_case(_results)

    @pytest.mark.slow_test
    def test_run_with_config_data_given_valid_files(
        self, simple_test_case_configs: tuple[NetworkConfigData, AnalysisConfigData]
    ):
        # 1. Run test.
        _results = Ra2ceHandler.run_with_config_data(
            simple_test_case_configs[0], simple_test_case_configs[1]
        )

        # 2. Verify expectations.
        self._validate_run_results_with_simple_test_case(_results)
