import shutil
from pathlib import Path

import pytest

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDirect,
    AnalysisSectionIndirect,
)
from ra2ce.analyses.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.graph.network_config_wrapper import NetworkConfigWrapper
from tests import test_data, test_results


class TestAnalysisConfigWrapper:
    def test_from_data_no_file_raises(self):
        with pytest.raises(FileNotFoundError):
            AnalysisConfigWrapper.from_data(Path("not_a_file"), None)

    def test_initialize(self):
        _config = AnalysisConfigWrapper()
        assert isinstance(_config, AnalysisConfigWrapper)
        assert isinstance(_config.config_data, AnalysisConfigData)

    @pytest.fixture(autouse=False)
    def valid_analysis_ini(self) -> Path:
        _ini_file = test_data / "acceptance_test_data" / "analyses.ini"
        assert _ini_file.exists()
        return _ini_file

    def test_from_data(self, valid_analysis_ini: Path):
        # 1. Define test data.
        _config_data = AnalysisConfigData()

        # 2. Run test.
        _config = AnalysisConfigWrapper.from_data(valid_analysis_ini, _config_data)

        # 3. Verify final expectations.
        assert isinstance(_config, AnalysisConfigWrapper)
        assert _config.config_data == _config_data
        assert _config.ini_file == valid_analysis_ini

    def test_from_data_with_network(self, valid_analysis_ini: Path):
        # 1. Define test data.
        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()

        # 2. Run test.
        _config = AnalysisConfigWrapper.from_data_with_network(
            valid_analysis_ini, _config_data, _network_config
        )

        # 3. Verify final expectations.
        assert isinstance(_config, AnalysisConfigWrapper)
        assert _config.config_data == _config_data
        assert _config.ini_file == valid_analysis_ini

    def test_from_data_without_network(self, valid_analysis_ini: Path):
        # 1. Define test data.
        _config_data = AnalysisConfigData()

        # 2. Run test.
        _config = AnalysisConfigWrapper.from_data_without_network(
            valid_analysis_ini, _config_data
        )

        # 3. Verify final expectations.
        assert isinstance(_config, AnalysisConfigWrapper)
        assert _config.config_data == _config_data
        assert _config.ini_file == valid_analysis_ini

    def test_configure(self, valid_analysis_ini: Path):
        # 1. Define test data.
        _config_data = AnalysisConfigData()
        _config = AnalysisConfigWrapper.from_data(valid_analysis_ini, _config_data)

        # 2. Run test.
        _config.configure()

    def test_initialize_output_dirs_with_valid_data(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data
        _analysis = AnalysisConfigWrapper()
        _output_dir = test_results / request.node.name
        _analysis.config_data = AnalysisConfigData(output_path=_output_dir)
        _analysis.config_data.analyses = [
            AnalysisSectionDirect(analysis="effectiveness_measures"),
            AnalysisSectionIndirect(analysis="single_link_redundancy"),
        ]
        if _output_dir.exists():
            shutil.rmtree(_output_dir)

        # 2. Run test
        _analysis.initialize_output_dirs()

        # 3. Verify expectations.
        assert _output_dir.exists()
        assert _output_dir.joinpath("effectiveness_measures").exists()
        assert _output_dir.joinpath("single_link_redundancy").exists()
