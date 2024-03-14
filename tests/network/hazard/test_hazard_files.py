from pathlib import Path

import pytest

from ra2ce.network.hazard.hazard_files import HazardFiles


class TestHazardFiles:
    @pytest.mark.parametrize(
        "hazard_map",
        [
            pytest.param([], id="Empty hazard map"),
            pytest.param([Path("a.tif")], id="One tif file"),
            pytest.param([Path("a.gpkg")], id="One gpkg file"),
            pytest.param([Path("a.csv")], id="One table file"),
            pytest.param([Path("a.tif"), Path("b.tif")], id="Two tif files"),
            pytest.param(
                [Path("a.tif"), Path("b.gpkg"), Path("c.csv")],
                id="Mix of files",
            ),
        ],
    )
    def test_create_from_hazard_map(self, hazard_map: list[Path]):
        # 1. Define test data.
        def get_extension_count(extension: str) -> int:
            if not hazard_map:
                return 0
            return sum(_hf.suffix == extension for _hf in hazard_map)

        # 2. Run test.
        _hazard_files = HazardFiles.from_hazard_map(hazard_map)

        # 3. Verify expectations.
        assert isinstance(_hazard_files, HazardFiles)
        assert len(_hazard_files.tif) == get_extension_count(".tif")
        assert len(_hazard_files.gpkg) == get_extension_count(".gpkg")
        assert len(_hazard_files.table) == get_extension_count(".csv")
