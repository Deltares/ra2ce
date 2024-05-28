from dataclasses import dataclass
from pathlib import Path

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDirect,
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_factory import AnalysisFactory
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol


class TestAnalysisFactory:
    @dataclass
    class MockAnalysisSectionDirect(AnalysisSectionDirect):
        analysis: AnalysisDamagesEnum = None

    @dataclass
    class MockAnalysisSectionIndirect(AnalysisSectionIndirect):
        analysis: AnalysisLossesEnum = None

    def test_get_direct_analysis_with_invalid_raises(self):
        # 1. Define test data.
        _analysis = self.MockAnalysisSectionDirect(analysis=AnalysisDamagesEnum.INVALID)
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc_err:
            AnalysisFactory.get_direct_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert str(exc_err.value) == "Analysis {} not implemented".format(
            _analysis.analysis
        )

    def test_get_indirect_analysis_with_invalid_raises(self):
        # 1. Define test data.
        _analysis = self.MockAnalysisSectionIndirect(
            analysis=AnalysisLossesEnum.INVALID
        )
        _config = AnalysisConfigWrapper()
        _config.config_data.output_path = Path("just a path")

        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc_err:
            AnalysisFactory.get_indirect_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert str(exc_err.value) == "Analysis {} not implemented".format(
            _analysis.analysis
        )

    def test_get_analysis_with_direct(self):
        # 1. Define test data.
        _analysis = self.MockAnalysisSectionDirect(
            analysis=AnalysisDamagesEnum.DIRECT_DAMAGE
        )
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        _result = AnalysisFactory.get_direct_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert isinstance(_result, AnalysisDirectProtocol)
        assert _result.graph_file_hazard == _config.graph_files.base_network_hazard
        assert _result.analysis == _analysis

    def test_get_analysis_with_indirect(self):
        # 1. Define test data.
        _analysis = self.MockAnalysisSectionIndirect(
            analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY
        )
        _config = AnalysisConfigWrapper()
        _config.config_data.output_path = Path("just a path")

        # 2. Run test.
        _result = AnalysisFactory.get_indirect_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert isinstance(_result, AnalysisIndirectProtocol)
        assert _result.graph_file == _config.graph_files.base_graph
        assert _result.analysis == _analysis
