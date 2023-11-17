import shutil

import pytest

from ra2ce.graph.graph_files import GraphFiles
from ra2ce.graph.network_config_wrapper import NetworkConfigWrapper
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
        assert isinstance(_result, GraphFiles)
        assert _result.base_graph is None
        assert _result.base_graph_hazard is None
        assert _result.origins_destinations_graph is None
        assert _result.origins_destinations_graph_hazard is None
        assert _result.base_network is None
        assert _result.base_network_hazard is None
        shutil.rmtree(_test_dir)
