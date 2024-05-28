import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.runners.analysis_runner_factory import AnalysisRunnerFactory
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner
from tests.runners.dummy_classes import DummyRa2ceInput


class TestAnalysisRunnerFactory:
    def test_get_runner_unknown_input_raises_error(self):
        with pytest.raises(ValueError) as exc_err:
            AnalysisRunnerFactory.get_runner(DummyRa2ceInput())

        assert (
            str(exc_err.value)
            == "No analysis runner found for the given configuration."
        )

    def test_get_runner_with_many_supported_runners_returns_analysis_runner_instance(
        self,
    ):
        # 1. Define test data.
        _config_wrapper = DummyRa2ceInput()
        _config_wrapper.analysis_config.config_data = AnalysisConfigData(
            analyses=[
                AnalysisSectionDamages(
                    analysis=AnalysisDamagesEnum.EFFECTIVENESS_MEASURES
                ),
                AnalysisSectionLosses(
                    analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY
                ),
            ]
        )
        _config_wrapper.network_config.config_data = NetworkConfigData()
        _config_wrapper.network_config.config_data.hazard.hazard_map = 4224

        # 2. Run test.
        _runner = AnalysisRunnerFactory.get_runner(_config_wrapper)

        # 3. Verify final expectations.
        assert isinstance(_runner, AnalysisRunner)
