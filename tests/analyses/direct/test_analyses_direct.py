from ra2ce.analyses.direct.analyses_direct import DirectAnalyses
from tests import test_data


class TestDirectAnalyses:
    def test_init(self):
        _config = {}
        _graphs = {}
        _analyses = DirectAnalyses(_config, _graphs)
        assert isinstance(_analyses, DirectAnalyses)

    def test_execute(self):
        _config = {
            "direct": [
                {
                    "name": "DummyExecute",
                    "analysis": "",
                    "save_shp": False,
                    "save_csv": False,
                }
            ],
            "output": test_data,
        }
        _graphs = {}
        DirectAnalyses(_config, _graphs).execute()
