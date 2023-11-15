import pytest

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDirect,
    AnalysisSectionIndirect,
    DirectAnalysisNameList,
    IndirectAnalysisNameList,
    ProjectSection,
)


class TestAnalysisConfigData:
    def test_initialize(self):
        _config_data = AnalysisConfigData()
        # At this moment it's not really mapped as a FOM.
        assert isinstance(_config_data, dict)
        assert isinstance(_config_data, AnalysisConfigData)

    @pytest.fixture
    def valid_config(self) -> AnalysisConfigData:
        _config = AnalysisConfigData(project=ProjectSection())
        for _indirect in IndirectAnalysisNameList:
            _config.analyses.append(AnalysisSectionIndirect(analysis=_indirect))
        for _direct in DirectAnalysisNameList:
            _config.analyses.append(AnalysisSectionDirect(analysis=_direct))
        yield _config

    def test_indirect(self, valid_config: AnalysisConfigData):
        # 1. Define test data

        # 2. Run test
        _indirect = [_config.analysis for _config in valid_config.indirect]

        # 3. Verify expectations
        assert all(item in _indirect for item in IndirectAnalysisNameList)

    def test_direct(self, valid_config: AnalysisConfigData):
        # 1. Define test data

        # 2. Run test
        _direct = [_config.analysis for _config in valid_config.direct]

        # 3. Verify expectations
        assert all(item in _direct for item in DirectAnalysisNameList)
