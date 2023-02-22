from ra2ce.configuration.network.readers.network_ini_config_reader import (
    NetworkIniConfigDataReader,
)


class TestNetworkIniConfigReader:
    def test_read_with_no_ini_file_returns_none(self):
        assert NetworkIniConfigDataReader().read(None) is None
