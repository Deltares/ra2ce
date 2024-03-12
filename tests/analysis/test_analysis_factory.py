from dataclasses import dataclass

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDirect,
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_direct_enum import (
    AnalysisDirectEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_indirect_enum import (
    AnalysisIndirectEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_factory import AnalysisFactory
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol


class TestAnalysisFactory:

    @dataclass
    class MockAnalysisSectionDirect(AnalysisSectionDirect):
        analysis: AnalysisDirectEnum = None

    @dataclass
    class MockAnalysisSectionIndirect(AnalysisSectionIndirect):
        analysis: AnalysisIndirectEnum = None

    def test_initialize(self):
        # 1.Define test data
        _analysis = self.MockAnalysisSectionDirect(analysis=AnalysisDirectEnum.DIRECT)

        # 2. Run test.
        _factory = AnalysisFactory(_analysis)

        # 3. Verify expectations.
        assert isinstance(_factory, AnalysisFactory)
        assert _factory.analysis == _analysis

    def test_get_analysis_with_invalid_raises(self):
        # 1. Define test data.
        _analysis = self.MockAnalysisSectionDirect(analysis=AnalysisDirectEnum.INVALID)
        _factory = AnalysisFactory(_analysis)
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        with pytest.raises(NotImplementedError):
            _factory.get_direct_analysis(_config)

    def test_get_analysis_with_direct(self):
        # 1. Define test data.
        _analysis = self.MockAnalysisSectionDirect(analysis=AnalysisDirectEnum.DIRECT)
        _factory = AnalysisFactory(_analysis)
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        _result = _factory.get_direct_analysis(_config)

        # 3. Verify expectations.
        assert isinstance(_result, AnalysisDirectProtocol)
        assert _result.graph_file == _config.graph_files.base_network_hazard
        assert _result.analysis == _analysis
