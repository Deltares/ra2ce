import shutil

import pytest

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDirect,
    AnalysisSectionIndirect,
)
from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_without_network import (
    AnalysisConfigWrapperWithoutNetwork,
)
from tests import acceptance_test_data, test_results


class TestAnalysisWithoutNetworkConfiguration:
    def test_init(self):
        _config = AnalysisConfigWrapperWithoutNetwork()
        assert isinstance(_config, AnalysisConfigWrapperWithoutNetwork)
        assert isinstance(_config.config_data, AnalysisConfigData)

    def test_given_no_ini_file_when_from_data_raises(self):
        with pytest.raises(FileNotFoundError):
            AnalysisConfigWrapperWithoutNetwork.from_data(
                acceptance_test_data / "non_existing_file.txt", None
            )

    def test_given_invalid_file_when_is_valid_then_false(self):
        class MockedConfigData(AnalysisConfigData):
            def is_valid(self) -> bool:
                return False

        # 1. Define test data.
        _config = AnalysisConfigWrapperWithoutNetwork()
        _config.config_data = MockedConfigData()
        _config.ini_file = acceptance_test_data / "not_a_file.ini"
        assert not _config.ini_file.exists()

        # 2. Run test and verify.
        assert not _config.is_valid()

    def test_initialize_output_dirs_with_valid_data(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data
        _analysis = AnalysisConfigWrapperWithoutNetwork()
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
