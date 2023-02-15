from ra2ce.analyses.indirect.analyses_indirect import IndirectAnalyses, Losses
from tests import test_data


class TestIndirectAnalyses:

    def test_initialize(self):
        # 1. Define test data.
        _graphs = {}
        _config = {
            "output": test_data
        }

        # 2. Run test.
        _indirect_analyses = IndirectAnalyses(_config, _graphs)

        # 3. Verify final expectations.
        assert isinstance(_indirect_analyses, IndirectAnalyses)
        