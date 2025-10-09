from dataclasses import dataclass, field

from ra2ce.analysis.analysis_config_data.adaptation_option_config_data import (
    AdaptationOptionConfigData,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.common.validation.validation_report import ValidationReport
from ra2ce.configuration.legacy_mappers import with_legacy_mappers


@with_legacy_mappers
@dataclass
class AdaptationConfigData(AnalysisConfigDataProtocol):
    """
    Configuration data for adaptation analysis.
    """

    name: str
    save_csv: bool = False  # Save results as CSV
    save_gpkg: bool = False  # Save results as GPKG

    losses_analysis: AnalysisLossesEnum = AnalysisLossesEnum.SINGLE_LINK_LOSSES

    # Economical settings
    time_horizon: float = 0.0
    discount_rate: float = 0.0
    # Hazard settings
    initial_frequency: float = 0.0
    climate_factor: float = 0.0
    hazard_fraction_cost: bool = False
    # First option is the no adaptation option
    adaptation_options: list[AdaptationOptionConfigData] = field(
        default_factory=list
    )

    def validate_integrity(self) -> ValidationReport:
        _report = ValidationReport()

        if not self.name:
            _report.error("An analysis 'name' must be provided.")

        return _report
