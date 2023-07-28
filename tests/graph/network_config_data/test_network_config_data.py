from ra2ce.graph.network_config_data.network_config_data import (
    CleanupSection,
    HazardSection,
    IsolationSection,
    NetworkConfigData,
    NetworkSection,
    OriginsDestinationsSection,
    ProjectSection,
)


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
