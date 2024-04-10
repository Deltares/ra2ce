import shutil

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import (
    AnalysisConfigDataReader,
)
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_config_data.network_config_data_reader import (
    NetworkConfigDataReader,
)
from ra2ce.ra2ce_handler import Ra2ceHandler
from tests import acceptance_test_data, test_results


class TestRa2ceHandler:
    def test_initialize_with_no_network_nor_analysis_does_not_raise(self):
        # 1. Run test.
        _handler = Ra2ceHandler(None, None)

        # 2. Verify final expectations.
        assert isinstance(_handler, Ra2ceHandler)

    @pytest.mark.parametrize(
        "analysis_config",
        [
            pytest.param(None, id="No analysis config"),
            pytest.param(NetworkConfigData(), id="Empty analysis config"),
        ],
    )
    @pytest.mark.parametrize(
        "network_config",
        [
            pytest.param(None, id="No network config"),
            pytest.param(NetworkConfigData(), id="Empty network config"),
        ],
    )
    def test_initialize_from_valid_config_does_not_raise(
        self, network_config, analysis_config
    ):
        # 1./2. Define test data/Run test.
        _handler = Ra2ceHandler.from_config(network_config, analysis_config)

        # 3. Verify expectations.
        assert isinstance(_handler, Ra2ceHandler)

    @pytest.fixture
    def network_config(
        self, request: pytest.FixtureRequest
    ) -> NetworkConfigData | None:
        if not request.param:
            return None
        _test_dir = acceptance_test_data
        _network_ini = acceptance_test_data.joinpath("network.ini")
        _network_config = NetworkConfigDataReader().read(_network_ini)
        _network_config.root_path = _test_dir.parent
        _network_config.input_path = _test_dir.joinpath("input")
        _network_config.static_path = _test_dir.joinpath("static")
        _network_config.output_path = _test_dir.joinpath("output")
        return _network_config

    @pytest.fixture
    def analysis_config(
        self, request: pytest.FixtureRequest
    ) -> AnalysisConfigData | None:
        if not request.param:
            return None
        _test_dir = acceptance_test_data
        _analysis_ini = acceptance_test_data.joinpath("analyses.ini")
        _analysis_config = AnalysisConfigDataReader().read(_analysis_ini)
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
        _test_dir = test_results / request.node.name
        _analysis_dir = _test_dir / "analysis_folder"
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
