from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDirect,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_direct_enum import (
    AnalysisDirectEnum,
)
from ra2ce.analysis.direct.analyses_direct import DirectAnalyses
from tests import test_data


class TestDirectAnalyses:
    def test_init(self):
        _config = {}
        _graphs = {}
        _analyses = DirectAnalyses(_config, _graphs)
        assert isinstance(_analyses, DirectAnalyses)

    def test_execute(self):
        _config = AnalysisConfigData(
            analyses=[
                AnalysisSectionDirect(
                    name="DummyExecute",
                    analysis=AnalysisDirectEnum.INVALID,
                    save_gpkg=False,
                    save_csv=False,
                )
            ],
            output_path=test_data,
        )
        _graphs = {}
        DirectAnalyses(_config, _graphs).execute()
