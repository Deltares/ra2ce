import shutil

import pytest

from ra2ce.io.writers.multi_graph_network_exporter import MultiGraphNetworkExporter
from ra2ce.io.writers.network_exporter_base import NetworkExporterBase
from ra2ce.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol
from tests import test_results


class TestMultigraphNetworkExporter:
    def test_initialize(self):
        _exporter = MultiGraphNetworkExporter("_basename", ["pickle", "shp"])
        assert isinstance(_exporter, MultiGraphNetworkExporter)
        assert isinstance(_exporter, NetworkExporterBase)
        assert isinstance(_exporter, Ra2ceExporterProtocol)

    def test_export_to_shp_creates_dir(self, request: pytest.FixtureRequest):
        """
        TODO: Create dummy export_data (MULTIGRAPH_TYPE) so we don't have to wrap it in a pytest.raises.
        """
        # 1. Define test data.
        _basename = "dummy_test"
        _exporter = MultiGraphNetworkExporter(_basename, ["pickle", "shp"])
        _test_dir = test_results / request.node.name
        if _test_dir.is_dir():
            shutil.rmtree(_test_dir)
        assert not _test_dir.exists()

        # 2. Run test.
        with pytest.raises(Exception):
            _exporter.export_to_shp(_test_dir, None)

        # 3. Verify expectations.
        assert _test_dir.exists()

    @pytest.mark.skip(
        reason="TODO: Not clear whether the pickle path should exist already or not."
    )
    def test_export_to_pickle(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _basename = "dummy_test"
        _exporter = MultiGraphNetworkExporter(_basename, ["pickle", "shp"])
        _test_dir = test_results / request.node.name
        if _test_dir.is_dir():
            shutil.rmtree(_test_dir)

        # 2. Run test.
        _exporter.export_to_pickle(_test_dir, None)

        # 3. Verify expectations.
        assert _test_dir.exists()
