from dataclasses import dataclass
from pathlib import Path

import pytest

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data import LossesConfigDataTypes
from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.damages_config_data import DamagesConfigData
from ra2ce.analysis.analysis_config_data.losses_analysis_config_data_protocol import (
    BaseLossesAnalysisConfigData,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_factory import AnalysisFactory
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol


class TestAnalysisFactory:

    def test_get_damages_analysis_with_invalid_raises(self):
        @dataclass
        class MockConfigData(AnalysisConfigDataProtocol):
            name: str = "mock"
        # 1. Define test data.
        _analysis = MockConfigData()
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc_err:
            AnalysisFactory.get_damages_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert str(exc_err.value) == "Analysis {} not implemented".format(
            _analysis
        )

    def test_get_losses_analysis_with_invalid_raises(self):
        # 1. Define test data.
        _analysis = BaseLossesAnalysisConfigData()
        _config = AnalysisConfigWrapper()
        _config.config_data.output_path = Path("just a path")

        # 2. Run test.
        with pytest.raises(NotImplementedError) as exc_err:
            AnalysisFactory.get_losses_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert str(exc_err.value) == "Analysis {} not implemented".format(
            _analysis
        )

    def test_get_analysis_with_damages(self):
        # 1. Define test data.
        _analysis = DamagesConfigData(name="sth")
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        _result = AnalysisFactory.get_damages_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert isinstance(_result, AnalysisDamagesProtocol)
        assert isinstance(_result, AnalysisBase)
        assert _result.graph_file_hazard == _config.graph_files.base_network_hazard
        assert _result.analysis == _analysis

    @pytest.mark.parametrize("analysis_type", [pytest.param(_analysis_type) for _analysis_type in LossesConfigDataTypes])
    def test_get_analysis_with_losses(self, analysis_type: type[BaseLossesAnalysisConfigData]):
        # 1. Define test data.
        _analysis = analysis_type(name= "sth")
        _config = AnalysisConfigWrapper()
        _config.config_data.output_path = Path("just a path")

        # 2. Run test.
        _result = AnalysisFactory.get_losses_analysis(_analysis, _config)

        # 3. Verify expectations.
        assert isinstance(_result, AnalysisLossesProtocol)
        assert isinstance(_result, AnalysisBase)
        assert isinstance(_result.analysis, BaseLossesAnalysisConfigData)
