import shutil

import pytest

from ra2ce.configuration.network.network_config import (
    NetworkConfig,
    hazard_handler,
    network_handler,
)
from tests import test_results


def test_network_handler_given_invalid_network_then_raises():
    with pytest.raises(Exception):
        network_handler({}, {})


def test_hazard_handler_given_invalid_values_returns_none():
    # 1. Define test data.
    _config_dict = {"hazard": {"hazard_map": None}}

    # 2. Run test.
    _return_value = hazard_handler(_config_dict, {}, {})

    # 3. Verify expectations
    assert _return_value is None


class TestNetworkConfig:
    def test_get_data_output(self):
        # 1. Define test data
        _test_ini = test_results / "non_existing.ini"
        _expected_value = test_results / "output"

        # 2. Run test
        _return_value = NetworkConfig.get_data_output(_test_ini)

        # 3. Verify expectations.
        assert _return_value == _expected_value

    def test_read_graphs_from_config_without_output_dir_raises(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data
        _test_dir = test_results / request.node.name
        if _test_dir.exists():
            shutil.rmtree(_test_dir)

        # 2. Run test
        with pytest.raises(ValueError) as exc_err:
            NetworkConfig.read_graphs_from_config(_test_dir)

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
        _result = NetworkConfig.read_graphs_from_config(_test_dir)

        # 3. Verify expectations
        assert isinstance(_result, dict)
        assert _result["base_graph"] is None
        assert _result["base_graph_hazard"] is None
        assert _result["origins_destinations_graph"] is None
        assert _result["origins_destinations_graph_hazard"] is None
        assert _result["base_network"] is None
        assert _result["base_network_hazard"] is None
        shutil.rmtree(_test_dir)
