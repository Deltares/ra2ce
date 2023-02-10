from ra2ce.analyses.direct.analyses_direct import DirectAnalyses


class TestDirectAnalyses:
    def test_init(self):
        _config = {}
        _graphs = {}
        _analyses = DirectAnalyses(_config, _graphs)
        assert isinstance(_analyses, DirectAnalyses)

    def test_execute(self):
        _config = {
            "direct": {"name": "DummyExecute", "save_shp": False, "save_csv": False}
        }
        _graphs = {}
        _analyses = DirectAnalyses(_config, _graphs)
        assert isinstance(_analyses, DirectAnalyses)
