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

from dataclasses import dataclass
from pathlib import Path

from ra2ce.analysis.analysis_config_data.base_origin_destination_config_data import (
    OptimalRouteOriginDestinationConfigData,
)
from ra2ce.common.validation.validation_report import ValidationReport


@dataclass
class EquityConfigData(OptimalRouteOriginDestinationConfigData):
    """Configuration data for equity analysis."""
    equity_weight: Path = None

    @property
    def config_name(self) -> str:
        return "equity"

    def validate_integrity(self) -> ValidationReport:
        _report = super().validate_integrity()
        if self.equity_weight is None:
            _report.error(
                f"For equity analysis '{self.name}': 'equity_weight' must be provided."
            )
        else:
            if (
                self.equity_weight.suffix.lower() != ".csv"
                or not self.equity_weight.exists()
            ):
                _report.error(
                    f"For equity analysis '{self.name}': 'equity_weight' file '{self.equity_weight}' is not a .csv file."
                )
        return _report
