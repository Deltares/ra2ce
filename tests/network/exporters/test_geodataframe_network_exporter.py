import shutil

import pytest
from geopandas import GeoDataFrame

from ra2ce.network.exporters.geodataframe_network_exporter import (
    GeoDataFrameNetworkExporter,
)
from ra2ce.network.exporters.network_exporter_base import NetworkExporterBase
from tests import test_results


class TestGeodataframeNetworkExporter:
    def test_initialize(self):
        _basename = "dummy_test"
        _exporter = GeoDataFrameNetworkExporter(_basename, ["pickle", "gpkg"])
        assert isinstance(_exporter, GeoDataFrameNetworkExporter)
        assert isinstance(_exporter, NetworkExporterBase)

    @pytest.mark.skip(reason="TODO: Needs to define GeoDataFrame dummydata.")
    def test_export_to_gpkg(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _output_dir = test_results / request.node.name
        if _output_dir.is_dir():
            shutil.rmtree(_output_dir)

        _basename = "dummy_test"
        _exporter = GeoDataFrameNetworkExporter(_basename, ["pickle", "gpkg"])

        _export_data = GeoDataFrame()

        # 2. Run test.
        _exporter.export_to_gpkg(_output_dir, _export_data)

        # 3. Verify final expectations.
        assert _output_dir.is_dir()
        assert (_output_dir / (_basename + ".gpkg")).is_file()

    @pytest.mark.skip(reason="TODO: Needs to define GeoDataFrame dummydata.")
    def test_export_to_pickle(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _output_dir = test_results / request.node.name
        if _output_dir.is_dir():
            shutil.rmtree(_output_dir)

        _basename = "dummy_test"
        _exporter = GeoDataFrameNetworkExporter(_basename, ["pickle", "gpkg"])

        _export_data = GeoDataFrame()

        # 2. Run test.
        _exporter.export_to_pickle(_output_dir, _export_data)

        # 3. Verify final expectations.
        assert _output_dir.is_dir()
        assert (_output_dir / (_basename + ".feather")).is_file()
