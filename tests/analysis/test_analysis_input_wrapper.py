from dataclasses import dataclass

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionBase
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.network.graph_files.graph_file import GraphFile


class TestAnalysisInputWrapper:

    @dataclass
    class MockAnalysisSection(AnalysisSectionBase):
        pass

    def test_initialize(self):
        # 1. Define test data
        _analysis = self.MockAnalysisSection()
        _config = AnalysisConfigWrapper()
        _graph_file = GraphFile(name="test_graph_file")
        _graph_file_hazard = GraphFile(name="test_graph_file_hazard")

        # 2. Run test
        _analysis_input = AnalysisInputWrapper(
            _analysis, _config, _graph_file, _graph_file_hazard
        )

        # 3. Verify expectations
        assert isinstance(_analysis_input, AnalysisInputWrapper)
        assert _analysis_input.analysis == _analysis
        assert _analysis_input.graph_file == _graph_file
        assert _analysis_input.graph_file_hazard == _graph_file_hazard
