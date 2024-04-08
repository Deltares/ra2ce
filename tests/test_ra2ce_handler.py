import shutil

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.ra2ce_handler import Ra2ceHandler
from tests import test_results


class TestRa2ceHandler:
    def test_initialize_with_no_network_nor_analysis_does_not_raise(self):
        # 1. Run test.
        _handler = Ra2ceHandler(None, None)

        # 2. Verify final expectations.
        assert isinstance(_handler, Ra2ceHandler)

    def test_initialize_from_config_does_not_raise(self):
        # 1. Define test data.
        _network_config = NetworkConfigData()
        _analysis_config = AnalysisConfigData()

        # 2. Run test.
        _handler = Ra2ceHandler.from_config(_network_config, _analysis_config)

        # 3. Verify expectations.
        assert isinstance(_handler, Ra2ceHandler)

    def test_initialize_with_analysis_does_not_raise(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        _test_dir = test_results / request.node.name
        _analysis_dir = _test_dir / "analysis_folder"
        if _test_dir.exists():
            shutil.rmtree(_test_dir)
        assert not _analysis_dir.exists()

        # 2. Run test.
        with pytest.raises(Exception):
            # It will raise an exception because the analysis folder does not
            # contain any analysis.ini file, but we only care to see if the
            # directory was correctly initialized.
            Ra2ceHandler(None, _analysis_dir)

        # 3. Verify expectations.
        assert _test_dir.exists()
        assert (_test_dir / "output").exists()
