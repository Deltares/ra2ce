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


from typing import Protocol, runtime_checkable

from ra2ce.configuration import AnalysisConfigBase
from ra2ce.configuration.config_wrapper import ConfigWrapper


@runtime_checkable
class AnalysisRunner(Protocol):
    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        """
        Validates whether the given `ConfigWrapper` is eligibile for this `AnalysisRunner`.

        Args:
            ra2ce_input (ConfigWrapper): Configuration desired to run.

        Returns:
            bool: Whether the `ConfigWrapper` can be run or not.
        """
        pass

    def run(self, analysis_config: AnalysisConfigBase) -> None:
        """
        Runs this `AnalysisRunner` with the given analysis configuration.

        Args:
            analysis_config (AnalysisConfigBase): Analysis configuration representation to be run on this `AnalysisRunner`.
        """
        pass
