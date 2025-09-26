import shutil
from pathlib import Path

import pytest

from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_results


class TestNetworkConfigWrapper:
    def test_read_graphs_from_config_without_output_dir_raises(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data
        _test_dir = test_results / request.node.name
        if _test_dir.exists():
            shutil.rmtree(_test_dir)

        # 2. Run test
        with pytest.raises(ValueError) as exc_err:
            NetworkConfigWrapper.read_graphs_from_config(_test_dir)

        # 3. Verify expectations.
        assert str(exc_err.value) == "Path does not exist: {}".format(_test_dir)

    def test_read_graphs_with_existing_dir_without_files(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data
        _test_dir = test_results / request.node.name
        if not _test_dir.exists():
            _test_dir.mkdir(parents=True)

        # 2. Run test.
        _result = NetworkConfigWrapper.read_graphs_from_config(_test_dir)

        # 3. Verify expectations
        assert isinstance(_result, GraphFilesCollection)
        assert _result.base_graph.graph is None
        assert _result.base_graph_hazard.graph is None
        assert _result.origins_destinations_graph.graph is None
        assert _result.origins_destinations_graph_hazard.graph is None
        assert _result.base_network.graph is None
        assert _result.base_network_hazard.graph is None
        shutil.rmtree(_test_dir)

    def test_analysis_config_wrapper_valid_without_ini_file(self):
        # 1. Define test data
        _network_wrapper = NetworkConfigWrapper()
        _network_wrapper.config_data = NetworkConfigData(
            root_path=Path("dummy_path"),
            static_path=Path("dummy_path"),
        )
        _network_wrapper.config_data.network.source = SourceEnum.OSB_BPF
        _network_wrapper.ini_file = None

        # 2. Run test.
        _result = _network_wrapper.is_valid()

        # 3. Verify expectations.
        assert _result is True
