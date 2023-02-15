import shutil

import pytest

from ra2ce.graph.osm_utils import from_shapefile_to_poly
from tests import test_data, test_results


class TestOsmUtils:
    @pytest.mark.skip(reason="TODO: Add missing test data.")
    def test_from_shapefile_to_poly(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _test_folder = test_data / "1000_zuid_holland"
        assert _test_folder.is_dir()

        _network_ini = _test_folder / "network.ini"
        assert _network_ini.exists()

        _input_dir = _test_folder / "input"
        assert _input_dir.exists()

        _test_shapefile = _input_dir / "zuid_holland_redundancy_epsg4326_wgs84.shp"
        assert _test_shapefile.exists()

        _output_dir = test_results / request.node.name
        if _output_dir.exists():
            shutil.rmtree(_output_dir)
        _output_dir.mkdir(parents=True)

        # 2. Run test.
        from_shapefile_to_poly(_test_shapefile, _output_dir, "zh_")
        assert any(_input_dir.glob(".poly"))

        # 3. Verify expectations.
        # TODO: This should be a second test
        _test_executables = test_data / "osm_executables"
        assert _test_executables.is_dir()
        input_osm_pbf = _input_dir / "netherlands.osm.pbf"
        out_type = "pbf"  # or 'o5m'

        osm_convert_exe = _test_executables / "osmconvert64.exe"
        polyfile = _input_dir / "zh_1.poly"
        outfile = _input_dir / (polyfile.stem + "." + out_type)
        assert osm_convert_exe.exists()
        assert polyfile.exists()

    def test_from_shapefile_to_poly(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _shp_file = (
            test_data / "acceptance_test_data" / "static" / "network" / "origins.shp"
        )
        assert _shp_file.exists()
        _output = test_results / request.node.name
        if _output.exists():
            shutil.rmtree(_output)
        _output.mkdir(parents=True)

        # 2. Run test.
        from_shapefile_to_poly(_shp_file, _output)

        # 3. Verify final expectations.
        assert any(_output.glob("*"))
