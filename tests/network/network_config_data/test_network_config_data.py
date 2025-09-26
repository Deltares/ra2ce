from ra2ce.network.network_config_data.network_config_data import (
    CleanupSection,
    HazardSection,
    IsolationSection,
    NetworkConfigData,
    NetworkSection,
    OriginsDestinationsSection,
    ProjectSection,
)
from tests import test_results


class TestNetworkConfigData:
    def test_initialize(self):
        _config_data = NetworkConfigData()

        # Verify expectations.
        assert _config_data.static_path is None
        assert isinstance(_config_data.project, ProjectSection)
        assert isinstance(_config_data.network, NetworkSection)
        assert isinstance(_config_data.origins_destinations, OriginsDestinationsSection)
        assert isinstance(_config_data.isolation, IsolationSection)
        assert isinstance(_config_data.hazard, HazardSection)
        assert isinstance(_config_data.cleanup, CleanupSection)

    def test_get_data_output(self):
        # 1. Define test data
        _test_ini = test_results / "non_existing.ini"
        _expected_value = test_results / "output"

        # 2. Run test
        _return_value = NetworkConfigData.get_data_output(_test_ini)

        # 3. Verify expectations.
        assert _return_value == _expected_value
