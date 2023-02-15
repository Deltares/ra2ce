from pathlib import Path

from ra2ce.graph.hazard import Hazard


class TestHazard:
    def test_initialize(self):
        # 1. Define test data.
        _config = {
            "hazard": {"aggregate_wl": "max", "hazard_map": [Path("file_01.csv")]},
        }
        _graphs = {}
        _files = {}

        # 2. Run test.
        _hazard = Hazard(_config, _graphs, _files)

        # 3. Verify final expectations.
        assert isinstance(_hazard, Hazard)
        assert any(_hazard.hazard_names)
        assert any(_hazard.ra2ce_names)
        assert any(_hazard.hazard_files)
