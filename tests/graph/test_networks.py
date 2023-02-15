import shutil

import pytest

from ra2ce.graph.networks import Network
from tests import test_results


class TestNetworks:
    def test_initialize(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _test_dir = test_results / "test_networks" / request.node.name
        _config = {
            "static": _test_dir / "static",
            "origins_destinations": {
                "origins": None,
                "destinations": None,
                "origins_names": None,
                "destinations_names": None,
                "id_name_origin_destination": None,
                "category": "dummy_category",
                "region": "",
            },
            "cleanup": {"snapping_threshold": None, "segmentation_length": None},
        }
        _files = []

        if _test_dir.exists():
            shutil.rmtree(_test_dir)

        # 2. Run test.
        _network = Network(_config, _files)

        # 3. Verify expectations
        assert isinstance(_network, Network)
        assert _network.od_category == "dummy_category"

    def test_initialize_without_category(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _test_dir = test_results / "test_networks" / request.node.name
        _config = {
            "static": _test_dir / "static",
            "origins_destinations": {
                "origins": None,
                "destinations": None,
                "origins_names": None,
                "destinations_names": None,
                "id_name_origin_destination": None,
                "region": "",
            },
            "cleanup": {"snapping_threshold": None, "segmentation_length": None},
        }
        _files = []

        if _test_dir.exists():
            shutil.rmtree(_test_dir)

        # 2. Run test.
        _network = Network(_config, _files)

        # 3. Verify expectations
        assert isinstance(_network, Network)
