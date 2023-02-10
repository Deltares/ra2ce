import os
import shutil

import pytest

from ra2ce.graph.osm_utils import from_shapefile_to_poly
from tests import test_data, test_results


class TestOsmUtils:
    @pytest.mark.skip(reason="TODO: Missing test data.")
    def test_from_shapefile_to_poly(self, request: pytest.FixtureRequest):
        ### Used for a Zuid-Holland test.
        # Find the network.ini and analysis.ini files

        _test_folder = test_data / "1000_zuid_holland"
        _network_ini = _test_folder / "network.ini"
        analyses_ini = None

        # root_path = get_root_path(network_ini, analyses_ini)

        # if network_ini:
        #    config_network = load_config(root_path, config_path=network_ini)

        #############################################################################
        # STEP 1: Convert shapefile to .poly file(s)
        # shapefile = data_folder / 'input' / 'zuid_holland_epsg4326_wgs84.shp'
        shapefile = (
            _test_folder / "input" / "zuid_holland_redundancy_epsg4326_wgs84.shp"
        )
        assert shapefile.exists()

        _results_dir = test_results / request.node.name
        if _results_dir.exists():
            shutil.rmtree(_results_dir)

        # 2. Run test.
        from_shapefile_to_poly(shapefile, _results_dir, "zh_")

        # 3. Verify expectations.
        assert _results_dir.exists()
        assert any(_results_dir.glob(".poly"))

        #############################################################################
        # STEP 2: Use .poly file to cut down the osm.pbf
        input_osm_pbf = _test_folder / "input" / "netherlands.osm.pbf"
        out_type = "pbf"  # or 'o5m'

        osm_convert_exe = test_data / "osm_executables" / "osmconvert64.exe"
        polyfile = _test_folder / "input" / "zh_1.poly"
        outfile = _test_folder / "input" / (polyfile.stem + "." + out_type)
        assert osm_convert_exe.exists()
        assert polyfile.exists()

        # For documentation on how the executable works, see this wiki: https://wiki.openstreetmap.org/wiki/Osmconvert
        os.system(
            "{}  {} -B={} --complete-ways --drop-broken-refs --hash-memory=10000 --out-{} -o={}".format(
                str(osm_convert_exe),
                str(input_osm_pbf),
                str(polyfile),
                out_type,
                str(outfile),
            )
        )
