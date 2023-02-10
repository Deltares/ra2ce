import shutil

import pytest

from ra2ce.io.writers.json_exporter import JsonExporter
from ra2ce.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol
from tests import test_results


class TestJsonExporter:
    def test_initialize(self):
        _json_exporter = JsonExporter()
        assert isinstance(_json_exporter, JsonExporter)
        assert isinstance(_json_exporter, Ra2ceExporterProtocol)

    def test_export(self, request: pytest.FixtureRequest):
        # 1. Define test data
        _test_dir = test_results / request.node.name
        if _test_dir.is_dir():
            shutil.rmtree(_test_dir)
        _test_file = _test_dir / "exported_data.json"
        _dummy_data = {"a": 123, "b": 456}

        # 2. Run test.
        JsonExporter().export(_test_file, _dummy_data)

        # 3. Verify expectations.
        assert _test_file.exists()
