from pathlib import Path
from ra2ce.graph.network_config_data.network_config_data import (
    CleanupSection,
    HazardSection,
    IsolationSection,
    NetworkConfigData,
    NetworkSection,
    OriginsDestinationsSection,
    ProjectSection,
)
import pytest
from tests import test_data


class TestNetworkConfigData:
    def test_initialize(self):
        _config_data = NetworkConfigData()

        # Verify expectations.
        assert _config_data.input_path is None
        assert _config_data.output_path is None
        assert _config_data.static_path is None
        assert isinstance(_config_data.project, ProjectSection)
        assert isinstance(_config_data.network, NetworkSection)
        assert isinstance(_config_data.origins_destinations, OriginsDestinationsSection)
        assert isinstance(_config_data.isolation, IsolationSection)
        assert isinstance(_config_data.hazard, HazardSection)
        assert isinstance(_config_data.cleanup, CleanupSection)

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
    def test_from_ini_file(self, network_ini_filepath: Path):
        _config_data = NetworkConfigData.from_ini_file(network_ini_filepath)
        assert isinstance(_config_data, NetworkConfigData)
