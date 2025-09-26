from pathlib import Path

from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_wrappers.network_wrapper_protocol import (
    NetworkWrapperProtocol,
)
from ra2ce.network.network_wrappers.shp_network_wrapper import ShpNetworkWrapper


class TestShpNetworkWrapper:
    def test_init(self):
        # 1.Define test data.
        _config_data = NetworkConfigData(
            root_path=Path("test_root_path"),
            static_path=Path("test_static_path"),
        )

        # 2. Run test.
        _wrapper = ShpNetworkWrapper(_config_data)

        # 3. Verify expectations.
        assert isinstance(_wrapper, ShpNetworkWrapper)
        assert isinstance(_wrapper, NetworkWrapperProtocol)
        assert _wrapper.crs.to_epsg() == 4326
