from dataclasses import dataclass
from pathlib import Path

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_factory import AnalysisFactory
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol


class TestAnalysisFactory:
    @dataclass
    class MockAnalysisSectionDirect(AnalysisSectionDamages):
        analysis: AnalysisDamagesEnum = None

    @dataclass
    class MockAnalysisSectionIndirect(AnalysisSectionLosses):
        analysis: AnalysisLossesEnum = None

    def test_get_damages_analysis_with_invalid_raises(self):
        # 1. Define test data.
        _analysis = self.MockAnalysisSectionDirect(analysis=AnalysisDamagesEnum.INVALID)
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc_err:
            AnalysisFactory.get_damages_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert str(exc_err.value) == "Analysis {} not implemented".format(
            _analysis.analysis
        )

    def test_get_losses_analysis_with_invalid_raises(self):
        # 1. Define test data.
        _analysis = self.MockAnalysisSectionIndirect(
            analysis=AnalysisLossesEnum.INVALID
        )
        _config = AnalysisConfigWrapper()
        _config.config_data.output_path = Path("just a path")

        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc_err:
            AnalysisFactory.get_losses_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert str(exc_err.value) == "Analysis {} not implemented".format(
            _analysis.analysis
        )

    def test_get_analysis_with_damages(self):
        # 1. Define test data.
        _analysis = self.MockAnalysisSectionDirect(analysis=AnalysisDamagesEnum.DAMAGES)
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        _result = AnalysisFactory.get_damages_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert isinstance(_result, AnalysisDamagesProtocol)
        assert _result.graph_file_hazard == _config.graph_files.base_network_hazard
        assert _result.analysis == _analysis

    def test_get_analysis_with_losses(self):
        # 1. Define test data.
        _analysis = self.MockAnalysisSectionIndirect(
            analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY
        )
        _config = AnalysisConfigWrapper()
        _config.config_data.output_path = Path("just a path")

        # 2. Run test.
        _result = AnalysisFactory.get_losses_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert isinstance(_result, AnalysisLossesProtocol)
        assert _result.graph_file == _config.graph_files.base_graph
        assert _result.analysis == _analysis
