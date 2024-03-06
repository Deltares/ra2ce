from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.indirect.analyses_indirect import IndirectAnalyses
from tests import test_data


class TestIndirectAnalyses:
    def test_initialize(self):
        # 1. Define test data.
        _graphs = {}
        _config = AnalysisConfigData(output_path=test_data)

        # 2. Run test.
        _indirect_analyses = IndirectAnalyses(_config, _graphs)

        # 3. Verify final expectations.
        assert isinstance(_indirect_analyses, IndirectAnalyses)
