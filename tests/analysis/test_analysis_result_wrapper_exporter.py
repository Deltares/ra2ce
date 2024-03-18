from ra2ce.analysis.analysis_result_wrapper_exporter import (
    AnalysisResultWrapperExporter,
)


class TestAnalysisResultWrapperExporter:

    def test_initialize(self):
        _exporter = AnalysisResultWrapperExporter()
        assert isinstance(_exporter, AnalysisResultWrapperExporter)
