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
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.base_rootable_paths import BaseRootablePaths
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.common.validation.validation_report import ValidationReport


@dataclass
class DamagesConfigData(BaseRootablePaths, AnalysisConfigDataProtocol):
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

    @property
    def config_name(self) -> str:
        return AnalysisDamagesEnum.DAMAGES.config_value

    def reroot_fields(self, old_root: Path, new_root: Path):
        _new_root = self._get_new_root(old_root, new_root.joinpath(self.config_name))
        if self.file_name is not None:
            self.file_name = _new_root.joinpath(self.file_name.name)

    def validate_integrity(self) -> ValidationReport:
        _report = ValidationReport()

        if not self.name:
            _report.error("An analysis 'name' must be provided.")

        if (
            not isinstance(self.event_type, EventTypeEnum)
            or self.event_type == EventTypeEnum.INVALID
            or self.event_type == EventTypeEnum.NONE
        ):
            _report.error(
                f"For damage analysis '{self.name}': 'event_type' must be a valid EventTypeEnum value."
            )
        if (
            not isinstance(self.damage_curve, DamageCurveEnum)
            or self.damage_curve == DamageCurveEnum.INVALID
        ):
            _report.error(
                f"For damage analysis '{self.name}': 'damage_curve' must be a valid DamageCurveEnum value."
            )

        if self.risk_calculation_mode == RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR:
            if self.risk_calculation_year is None or self.risk_calculation_year <= 0:
                _report.error(
                    f"For damage analysis '{self.name}': 'risk_calculation_year' should be a positive integer when 'risk_calculation_mode' is set to 'RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR'."
                )
        return _report
