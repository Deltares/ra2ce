import shutil

import pytest

from ra2ce.configuration.network.network_config import NetworkConfig
from tests import test_results


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
