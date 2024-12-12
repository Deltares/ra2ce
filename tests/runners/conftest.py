import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDamages,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper


class DummyAnalysisConfigWrapper(AnalysisConfigWrapper):
    def __init__(self) -> None:
        self.config_data = AnalysisConfigData(analyses=[])

    @classmethod
    def from_data(cls, **kwargs):
        raise NotImplementedError()

    def configure(self) -> None:
        raise NotImplementedError()

    def is_valid(self) -> bool:
        raise NotImplementedError()


class DummyRa2ceInput(ConfigWrapper):
    def __init__(self) -> None:
        self.analysis_config = DummyAnalysisConfigWrapper()
        self.network_config = NetworkConfigWrapper()


@pytest.fixture(name="dummy_ra2ce_input")
def _get_dummy_ra2ce_input() -> ConfigWrapper:
    _ra2ce_input = DummyRa2ceInput()
    assert isinstance(_ra2ce_input, ConfigWrapper)
    return _ra2ce_input


@pytest.fixture(name="damages_ra2ce_input")
def _get_dummy_ra2ce_input_with_damages(
    dummy_ra2ce_input: ConfigWrapper,
) -> ConfigWrapper:
    dummy_ra2ce_input.analysis_config.config_data.analyses = [
        AnalysisSectionDamages(
            analysis=AnalysisDamagesEnum.DAMAGES,
            name="Damages",
            event_type=EventTypeEnum.EVENT,
            damage_curve=DamageCurveEnum.MAN,
            save_csv=True,
            save_gpkg=True,
        )
    ]
    dummy_ra2ce_input.network_config.config_data.hazard.hazard_map = "A value"
    return dummy_ra2ce_input
