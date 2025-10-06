"""
                GNU GENERAL PUBLIC LICENSE
                  Version 3, 29 June 2007

Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
Copyright (C) 2023 Stichting Deltares

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataWithIntegrityValidationProtocol,
)
from ra2ce.analysis.analysis_config_data.config_data_integrity_validators import (
    validate_risk_calculation,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.common.validation.validation_report import ValidationReport
from ra2ce.configuration.legacy_mappers import with_legacy_mappers


@with_legacy_mappers
@dataclass
class DamagesConfigData(AnalysisConfigDataWithIntegrityValidationProtocol):
    """
    Configuration data for damages analysis.
    """

    # Common properties
    name: str
    save_gpkg: bool = False  # Save results as GPKG
    save_csv: bool = False  # Save results as CSV

    # Concrete properties
    event_type: EventTypeEnum = field(default_factory=lambda: EventTypeEnum.NONE)
    damage_curve: DamageCurveEnum = field(
        default_factory=lambda: DamageCurveEnum.INVALID
    )

    # road damage
    risk_calculation_mode: RiskCalculationModeEnum = field(
        default_factory=lambda: RiskCalculationModeEnum.NONE
    )
    # Risk calculation year is required if 'risk_calculation_mode' is set to 'RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR'
    risk_calculation_year: Optional[int] = None

    create_table: bool = False
    file_name: Optional[Path] = None
    representative_damage_percentage: float = 100

    @validate_risk_calculation
    def validate_integrity(self) -> ValidationReport:
        _report = ValidationReport()
        return _report
