import pytest

from ra2ce.io.writers.network_exporter_base import NetworkExporterBase
from ra2ce.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol


class TestNetworkExporterBase:
    def test_initialize(self):
        _exporter_base = NetworkExporterBase("a_name", [])
        assert isinstance(_exporter_base, NetworkExporterBase)
        assert isinstance(_exporter_base, Ra2ceExporterProtocol)
        assert _exporter_base._export_types == []

    @pytest.mark.parametrize("export_type", [("pickle"), ("shp")])
    def test_export_data(self, export_type: str):
        _exporter_base = NetworkExporterBase("a_name", [export_type])
        _result = _exporter_base.export(None, None)
        assert _result is None
        
