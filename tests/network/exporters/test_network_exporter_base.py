import pytest

from ra2ce.common.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol
from ra2ce.network.exporters.network_exporter_base import NetworkExporterBase
from tests import test_results


class TestNetworkExporterBase:
    def test_initialize(self):
        _exporter_base = NetworkExporterBase(basename="a_name", export_types=[])
        assert isinstance(_exporter_base, NetworkExporterBase)
        assert isinstance(_exporter_base, Ra2ceExporterProtocol)
        assert _exporter_base.export_types == []

    @pytest.mark.parametrize("export_type", [("pickle"), ("gpkg")])
    def test_export_data(self, export_type: str, request: pytest.FixtureRequest):
        # 1. Define test data.
        _output_dir = test_results / request.node.name

        # 2. Run test.
        _exporter_base = NetworkExporterBase(
            basename="a_name", export_types=[export_type]
        )
        _result = _exporter_base.export(_output_dir, None)

        # 3. Verify expectations.
        assert _result is None
