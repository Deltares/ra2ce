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

from __future__ import annotations

from dataclasses import dataclass, field

from ra2ce.analysis.adaptation.adaptation import Adaptation
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_enum import AnalysisEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_factory import AnalysisFactory
from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol


@dataclass
class AnalysisCollection:
    damages_analyses: list[AnalysisDamagesProtocol] = field(default_factory=list)
    losses_analyses: list[AnalysisLossesProtocol] = field(default_factory=list)
    adaptation_analysis: Adaptation = None

    @property
    def analyses(self) -> list[AnalysisProtocol]:
        """
        Get all analyses in the collection.

        Returns:
            list[AnalysisProtocol]: All analyses in the collection.
        """
        return self.damages_analyses + self.losses_analyses + [self.adaptation_analysis]

    @classmethod
    def from_config(
        cls, analysis_config: AnalysisConfigWrapper
    ) -> AnalysisCollection | None:
        """
        Create an AnalysisCollection from an AnalysisConfigWrapper.

        Args:
            analysis_config (AnalysisConfigWrapper): The analysis configuration.

        Returns:
            AnalysisCollection: Collection of analyses to be executed.
        """
        if not analysis_config:
            return None
        return cls(
            damages_analyses=[
                AnalysisFactory.get_damages_analysis(analysis, analysis_config)
                for analysis in analysis_config.config_data.damages_list
            ],
            losses_analyses=[
                AnalysisFactory.get_losses_analysis(analysis, analysis_config)
                for analysis in analysis_config.config_data.losses_list
            ],
            adaptation_analysis=AnalysisFactory.get_adaptation_analysis(
                analysis_config.config_data.adaptation, analysis_config
            ),
        )

    def get_analysis(
        self, analysis_type: AnalysisEnum | AnalysisDamagesEnum | AnalysisLossesEnum
    ) -> AnalysisProtocol | None:
        """
        Get a specific analysis from the collection.

        Args:
            analysis_type (AnalysisEnum | AnalysisDamagesEnum | AnalysisLossesEnum):
                The analysis that is requested.

        Raises:
            ValueError: The analysis type is not valid.

        Returns:
            AnalysisLossesProtocol | AnalysisDamagesProtocol | None:
                The requested analysis (if present).
        """
        if analysis_type == AnalysisEnum.ADAPTATION:
            return self.adaptation_analysis
        if isinstance(analysis_type, AnalysisDamagesEnum):
            return next((x for x in self.damages_analyses), None)
        if isinstance(analysis_type, AnalysisLossesEnum):
            return next((x for x in self.losses_analyses), None)
        raise ValueError(f"Analysis type {analysis_type} is not valid.")
