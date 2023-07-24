from configparser import ConfigParser
from pathlib import Path

import pytest

from ra2ce.common.configuration.ini_configuration_reader_protocol import (
    IniConfigurationReaderProtocol,
)
from ra2ce.graph.network_config_data.network_config_data import NetworkConfigData
from ra2ce.graph.network_config_data.network_config_data_reader import (
    NetworkConfigDataReader,
)
from tests import test_data


class TestNetworkConfigDataReader:
    def test_initialize(self):
        _reader = NetworkConfigDataReader()
        assert isinstance(_reader, NetworkConfigDataReader)
        assert isinstance(_reader, IniConfigurationReaderProtocol)
        assert isinstance(_reader._parser, ConfigParser)

    @pytest.fixture
    def network_ini_filepath(self, request: pytest.FixtureRequest) -> Path:
        network_ini = test_data.joinpath(request.param, "network.ini")
        assert network_ini.is_file()
        yield network_ini

    @pytest.mark.parametrize(
        "network_ini_filepath",
        [
            pytest.param("1_network_shape"),
            pytest.param("2_network_shape"),
            pytest.param("3_network_osm_download"),
        ],
        indirect=True,
    )
    def test_read(self, network_ini_filepath: Path):
        _config_data = NetworkConfigDataReader().read(network_ini_filepath)
        assert isinstance(_config_data, NetworkConfigData)
