from pathlib import Path

import pytest

from ra2ce.network.hazard.hazard_files import HazardFiles


class TestHazardFiles:
    @pytest.mark.parametrize(
        "hazard_map, tif, gpkg, table",
        [
            pytest.param([], 0, 0, 0, id="Empty hazard map"),
            pytest.param([Path("a.tif")], 1, 0, 0, id="One tif file"),
            pytest.param([Path("a.gpkg")], 0, 1, 0, id="One gpkg file"),
            pytest.param([Path("a.csv")], 0, 0, 1, id="One table file"),
            pytest.param([Path("a.tif"), Path("b.tif")], 2, 0, 0, id="Two tif files"),
            pytest.param(
                [Path("a.tif"), Path("b.gpkg"), Path("c.csv")],
                1,
                1,
                1,
                id="Mix of files",
            ),
        ],
    )
    def test_create_from_hazard_map(
        self, hazard_map: list[Path], tif: int, gpkg: int, table: int
    ):
        # 1. Define test data.

        # 2. Run test.
        _hazard_files = HazardFiles.from_hazard_map(hazard_map)

        # 3. Verify expectations.
        assert isinstance(_hazard_files, HazardFiles)
        assert len(_hazard_files.tif) == tif
        assert len(_hazard_files.gpkg) == gpkg
        assert len(_hazard_files.table) == table
