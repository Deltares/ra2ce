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
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.runners.analysis_runner_factory import AnalysisRunnerFactory
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class TestAnalysisRunnerFactory:
    def test_get_runner_unknown_input_raises_error(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        with pytest.raises(ValueError) as exc_err:
            AnalysisRunnerFactory.get_supported_runners(dummy_ra2ce_input)

        assert (
            str(exc_err.value)
            == "No analysis runner found for the given configuration."
        )

    def test_get_runner_with_many_supported_runners_returns_analysis_runner_instance(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        _config_wrapper = dummy_ra2ce_input
        _config_wrapper.analysis_config.config_data = AnalysisConfigData(
            analyses=[
                AnalysisSectionDamages(analysis=AnalysisDamagesEnum.DAMAGES),
                AnalysisSectionLosses(
                    analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY
                ),
            ]
        )
        _config_wrapper.network_config.config_data = NetworkConfigData()
        _config_wrapper.network_config.config_data.hazard.hazard_map = 4224

        # 2. Run test.
        _supported_runners = AnalysisRunnerFactory.get_supported_runners(
            _config_wrapper
        )

        # 3. Verify final expectations.
        assert isinstance(_supported_runners, list)
        assert len(_supported_runners) == 2
        assert all(issubclass(_sr, AnalysisRunner) for _sr in _supported_runners)
