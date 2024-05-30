import shutil
from pathlib import Path

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import (
    AnalysisConfigDataReader,
)
from ra2ce.analysis.analysis_result_wrapper import AnalysisResultWrapper
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

    def _get_acceptance_test_data_copy_dir(
        self, request: pytest.FixtureRequest
    ) -> Path:
        _copy_root_dir = test_results.joinpath(request.node.originalname)
        if not _copy_root_dir.is_dir():
            _copy_root_dir.mkdir(parents=True)
        _test_case_name = (
            request.node.name.split("[")[-1].split("]")[0].lower().replace(" ", "_")
        )
        _test_case_dir = _copy_root_dir.joinpath(_test_case_name)
        if not _test_case_dir.is_dir():
            shutil.copytree(test_data.joinpath("single_link_losses"), _test_case_dir)
        return _test_case_dir

    @pytest.fixture(name="network_config")
    def _get_network_config_fixture(
        self, request: pytest.FixtureRequest
    ) -> NetworkConfigData | None:
        if not request.param:
            return None
        _test_dir = self._get_acceptance_test_data_copy_dir(request)
        _network_config = NetworkConfigDataReader().read(
            _test_dir.joinpath("network.ini")
        )
        _network_config.root_path = _test_dir.parent
        _network_config.input_path = _test_dir.joinpath("input")
        _network_config.static_path = _test_dir.joinpath("static")
        _network_config.output_path = _test_dir.joinpath("output")
        return _network_config

    @pytest.fixture(name="analysis_config")
    def _get_analysis_config_fixture(
        self, request: pytest.FixtureRequest
    ) -> AnalysisConfigData | None:
        if not request.param:
            return None
        _test_dir = self._get_acceptance_test_data_copy_dir(request)
        _analysis_config = AnalysisConfigDataReader().read(
            _test_dir.joinpath("analyses.ini")
        )
        _analysis_config.static_path = _test_dir.joinpath("static")
        return _analysis_config

    @pytest.mark.slow_test
    @pytest.mark.parametrize(
        "analysis_config",
        [
            pytest.param(None, id="No analysis config"),
            pytest.param(
                True,
                id="Valid analysis config",
            ),
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "network_config",
        [
            pytest.param(None, id="No network config"),
            pytest.param(
                True,
                id="Valid network config",
            ),
        ],
        indirect=True,
    )
    def test_configure_handler_created_from_config_does_not_raise(
        self,
        network_config: NetworkConfigData,
        analysis_config: AnalysisConfigData,
    ):
        # 1./2. Define test data./Run test.
        _handler = Ra2ceHandler.from_config(network_config, analysis_config)
        _handler.configure()

        # 3. Verify expectations.
        assert isinstance(_handler, Ra2ceHandler)

    def test_initialize_with_analysis_does_not_raise(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        _test_dir = test_results.joinpath(request.node.name)
        _analysis_dir = _test_dir.joinpath("analysis_folder")
        if _test_dir.exists():
            shutil.rmtree(_test_dir)
        assert not _analysis_dir.exists()

        # 2. Run test.
        with pytest.raises(Exception):
            # It will raise an exception because the analysis folder does not
            # contain any analysis.ini file, but we only care to see if the
            # directory was correctly initialized.
            Ra2ceHandler(None, _analysis_dir)

        # 3. Verify expectations.
        assert _test_dir.exists()
        assert (_test_dir / "output").exists()

    @pytest.mark.slow_test
    def test_run_with_ini_files_given_valid_files(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _test_dir = self._get_acceptance_test_data_copy_dir(request)
        _network_file = _test_dir.joinpath("network.ini")
        _analyses_file = _test_dir.joinpath("analyses.ini")

        # 2. Run test.
        _results = Ra2ceHandler.run_with_ini_files(_network_file, _analyses_file)

        # 3. Verify expectations.
        assert any(_results)
        assert all(isinstance(_result, AnalysisResultWrapper) for _result in _results)

    @pytest.mark.slow_test
    def test_run_with_config_data_given_valid_files(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        _test_dir = self._get_acceptance_test_data_copy_dir(request)

        # Network configuration
        _network_file = _test_dir.joinpath("network.ini")
        assert _network_file.exists()
        _network_config_data = NetworkConfigDataReader().read(_network_file)
        assert isinstance(_network_config_data, NetworkConfigData)

        # Analysis configuration
        _analyses_file = _test_dir.joinpath("analyses.ini")
        assert _analyses_file.exists()
        _analysis_config_data = AnalysisConfigDataReader().read(_analyses_file)
        assert isinstance(_analysis_config_data, AnalysisConfigData)

        # 2. Run test.
        _results = Ra2ceHandler.run_with_config_data(
            _network_config_data, _analysis_config_data
        )

        # 3. Verify expectations.
        assert any(_results)
        assert all(isinstance(_result, AnalysisResultWrapper) for _result in _results)
