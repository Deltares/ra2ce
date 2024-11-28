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

import math
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptationOption,
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)


@dataclass
class AdaptationOption:
    id: str = ""
    name: str = ""
    construction_cost: float = 0.0
    maintenance_interval: float = math.inf
    maintenance_cost: float = 0.0
    damages_config: AnalysisSectionDamages = None
    losses_config: AnalysisSectionLosses = None

    @classmethod
    def from_config(
        cls,
        adaptation_option: AnalysisSectionAdaptationOption,
        damages_section: AnalysisSectionDamages,
        losses_section: AnalysisSectionLosses,
    ) -> AdaptationOption:
        # Add adaptation id to paths
        def extend_path(analysis: str, input_path: Path | None) -> Path | None:
            if not input_path:
                return None
            return input_path.parent.joinpath(
                adaptation_option.id, analysis, input_path.name
            )

        if not damages_section or not losses_section:
            raise ValueError(
                "Damages and losses sections are required to create an adaptation option."
            )

        _damages_section = deepcopy(damages_section)
        # TODO: who does this work with damages files?

        _losses_section = deepcopy(losses_section)
        _losses_section.resilience_curves_file = extend_path(
            "losses", losses_section.resilience_curves_file
        )
        _losses_section.traffic_intensities_file = extend_path(
            "losses", losses_section.traffic_intensities_file
        )
        _losses_section.values_of_time_file = extend_path(
            "losses", losses_section.values_of_time_file
        )

        return cls(
            id=adaptation_option.id,
            name=adaptation_option.name,
            construction_cost=adaptation_option.construction_cost,
            maintenance_interval=adaptation_option.maintenance_interval,
            maintenance_cost=adaptation_option.maintenance_cost,
            damages_config=_damages_section,
            losses_config=_losses_section,
        )
