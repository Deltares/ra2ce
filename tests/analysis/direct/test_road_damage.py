from ra2ce.analysis.direct.road_damage import DirectAnalyses


class TestRoadDamage:
    def test_initialize(self):
        """
        TODO: This test gives all signes `DirectAnalyses` class is not required.
        """
        _direct_analyses = DirectAnalyses({})
        assert isinstance(_direct_analyses, DirectAnalyses)
        _direct_analyses.execute()
