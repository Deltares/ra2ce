from ra2ce.configuration import NetworkIniConfigData


class TestNetworkIniConfigData:
    def test_initialize(self):
        _config_data = NetworkIniConfigData()
        # At this moment it's not really mapped as a FOM.
        assert isinstance(_config_data, dict)
        assert isinstance(_config_data, NetworkIniConfigData)

    def test_from_dict(self):
        _dict_values = {"the answer": 42}
        _config_data = NetworkIniConfigData.from_dict(_dict_values)

        assert isinstance(_config_data, NetworkIniConfigData)
        assert _config_data == _dict_values
