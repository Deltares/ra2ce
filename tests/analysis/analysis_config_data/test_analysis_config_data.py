import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDirect,
    AnalysisSectionIndirect,
    DirectAnalysisNameList,
    IndirectAnalysisNameList,
    ProjectSection,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from tests import test_results


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
            _config.analyses.append(
                AnalysisSectionIndirect(analysis=AnalysisLossesEnum.get_enum(_indirect))
            )
        for _direct in DirectAnalysisNameList:
            _config.analyses.append(
                AnalysisSectionDirect(analysis=AnalysisDamagesEnum.get_enum(_direct))
            )
        yield _config

    def test_indirect(self, valid_config: AnalysisConfigData):
        # 1. Define test data

        # 2. Run test
        _indirect = [_config.analysis.config_value for _config in valid_config.indirect]

        # 3. Verify expectations
        assert all(item in _indirect for item in IndirectAnalysisNameList)

    def test_direct(self, valid_config: AnalysisConfigData):
        # 1. Define test data

        # 2. Run test
        _direct = [_config.analysis.config_value for _config in valid_config.direct]

        # 3. Verify expectations
        assert all(item in _direct for item in DirectAnalysisNameList)

    def test_get_data_output(self):
        # 1. Define test data
        _test_ini = test_results / "non_existing.ini"
        _expected_value = test_results / "output"

        # 2. Run test
        _return_value = AnalysisConfigData.get_data_output(_test_ini)

        # 3. Verify expectations.
        assert _return_value == _expected_value
