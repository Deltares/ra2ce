import shutil

import pytest

from ra2ce.configuration.analysis.analysis_config_base import AnalysisConfigBase
from ra2ce.configuration.config_protocol import ConfigProtocol
from tests import test_data, test_results


class TestAnalysisConfigBase:
    def test_initialize(self):
        _analysis = AnalysisConfigBase()
        assert isinstance(_analysis, AnalysisConfigBase)
        assert isinstance(_analysis, ConfigProtocol)

    def test_get_data_output(self):
        # 1. Define test data.
        _ini_file = test_data / "acceptance_test_data" / "network.ini"
        assert _ini_file.exists()

        # 2. Run test.
        _output_path = AnalysisConfigBase.get_data_output(_ini_file)

        # 3. Verify final expectations.
        assert _output_path.name == "output"

    def test_initialize_output_dirs_no_analysis_type(self):
        # 1. Define test data
        _analysis = AnalysisConfigBase()
        _analysis.config_data = {}

        # 2. Run test
        _analysis.initialize_output_dirs()

    def test_initialize_output_dirs_with_valid_data(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data
        _analysis = AnalysisConfigBase()
        _output_dir = test_results / request.node.name
        _analysis.config_data = {
            "direct": [{"analysis": "test_direct"}],
            "indirect": [{"analysis": "test_indirect"}],
            "output": _output_dir,
        }
        if _output_dir.exists():
            shutil.rmtree(_output_dir)

        # 2. Run test
        _analysis.initialize_output_dirs()

        # 3. Verify expectations.
        assert _output_dir.exists()
        assert (_output_dir / "test_direct").exists()
        assert (_output_dir / "test_indirect").exists()
