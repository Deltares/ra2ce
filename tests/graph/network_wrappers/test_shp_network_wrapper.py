from ra2ce.graph.network_config_data.network_config_data import (
    NetworkConfigData,
)
from ra2ce.graph.network_wrappers.network_wrapper_protocol import NetworkWrapperProtocol
from ra2ce.graph.network_wrappers.shp_network_wrapper import ShpNetworkWrapper


class TestShpNetworkWrapper:
    def test_init(self):
        # 1.Define test data.
        _config_data = NetworkConfigData()

        # 2. Run test.
        _wrapper = ShpNetworkWrapper(_config_data)

        # 3. Verify expectations.
        assert isinstance(_wrapper, ShpNetworkWrapper)
        assert isinstance(_wrapper, NetworkWrapperProtocol)
        assert _wrapper.crs.to_epsg() == 4326
