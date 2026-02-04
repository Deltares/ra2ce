"""
                GNU GENERAL PUBLIC LICENSE
                  Version 3, 29 June 2007

Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
Copyright (C) 2023-2026 Stichting Deltares

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

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.common.validation.validation_report import ValidationReport
from ra2ce.configuration.legacy_mappers import with_legacy_mappers


@with_legacy_mappers
@dataclass
class SingleLinkRedundancyConfigData(AnalysisConfigDataProtocol):
    """
    Reflects all possible settings that a single link redundancy config might contain.
    """

    # Common properties
    name: str
    save_gpkg: bool = False
    save_csv: bool = False

    # Concrete properties
    weighing: WeighingEnum = field(default_factory=lambda: WeighingEnum.NONE)

    def validate_integrity(self) -> ValidationReport:
        _report = ValidationReport()
        if not self.name:
            _report.error("An analysis 'name' must be provided.")
        if (
            not isinstance(self.weighing, WeighingEnum)
            or self.weighing == WeighingEnum.INVALID
            or self.weighing == WeighingEnum.NONE
        ):
            _report.error(
                f"For single link redundancy analysis '{self.name}': 'weighing' must be a valid WeighingEnum value."
            )
        return _report
