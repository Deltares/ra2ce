from dataclasses import dataclass
from pathlib import Path

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionBase
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper


class TestAnalysisInputWrapper:

    @dataclass
    class MockAnalysisSection(AnalysisSectionBase):
        pass

    def test_initialize(self):
        # 1. Define test data
        _analysis = self.MockAnalysisSection()
        _config = AnalysisConfigWrapper()
        _config.config_data.output_path = Path("just a path")

        # 2. Run test
        _analysis_input = AnalysisInputWrapper(_analysis, _config)

        # 3. Verify expectations
        assert isinstance(_analysis_input, AnalysisInputWrapper)
