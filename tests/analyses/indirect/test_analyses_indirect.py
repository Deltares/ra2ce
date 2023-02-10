from ra2ce.analyses.indirect.analyses_indirect import IndirectAnalyses
from tests import test_data


class TestAnalysesIndirect:

    def test_initialize_indirect_analyses(self):
        # 1. Define test data.
        _graphs = {}
        _config = {
            "output": test_data
        }

        # 2. Run test.
        _indirect_analyses = IndirectAnalyses(_config, _graphs)

        # 3. Verify final expectations.
        assert isinstance(_indirect_analyses, IndirectAnalyses)
