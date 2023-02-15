import networkx as nx
import pytest
from geopandas import GeoDataFrame
from networkx.classes import multidigraph, multigraph

from ra2ce.io.writers.geodataframe_network_exporter import GeoDataFrameNetworkExporter
from ra2ce.io.writers.multi_graph_network_exporter import MultiGraphNetworkExporter
from ra2ce.io.writers.network_exporter_base import NETWORK_TYPE, NetworkExporterBase
from ra2ce.io.writers.network_exporter_factory import NetworkExporterFactory


class TestNetworkExporterFactory:
    @pytest.mark.parametrize(
        "network_type, expected_exporter",
        [
            pytest.param(GeoDataFrame, GeoDataFrameNetworkExporter, id="GeoDataFrame"),
            pytest.param(
                multigraph.MultiGraph, MultiGraphNetworkExporter, id="MultiGraph"
            ),
            pytest.param(
                multidigraph.MultiDiGraph, MultiGraphNetworkExporter, id="MultiDiGraph"
            ),
        ],
    )
    def test_get_exporter(self, network_type: NETWORK_TYPE, expected_exporter):
        _result = NetworkExporterFactory.get_exporter(network_type())
        assert _result is expected_exporter
        assert issubclass(_result, NetworkExporterBase)
