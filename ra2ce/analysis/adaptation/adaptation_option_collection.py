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

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)


@dataclass
class AdaptationOptionCollection:
    """
    Collection of adaptation options with all their related properties.
    """

    discount_rate: float = 0.0
    time_horizon: float = 0.0
    climate_factor: float = 0.0
    initial_frequency: float = 0.0
    no_adaptation_option: AdaptationOption = None
    adaptation_options: list[AdaptationOption] = field(default_factory=list)

    @classmethod
    def from_config(
        cls,
        analysis_config_data: AnalysisConfigData,
    ) -> AdaptationOptionCollection:
        if not analysis_config_data.adaptation:
            raise ValueError("No adaptation section found in the analysis config data.")
        _collection = cls(
            discount_rate=analysis_config_data.adaptation.discount_rate,
            time_horizon=analysis_config_data.adaptation.time_horizon,
            climate_factor=analysis_config_data.adaptation.climate_factor,
            initial_frequency=analysis_config_data.adaptation.initial_frequency,
        )

        for i, _config_option in enumerate(
            analysis_config_data.adaptation.adaptation_options
        ):
            _option = AdaptationOption.from_config(
                _config_option,
                analysis_config_data.get_analysis(AnalysisDamagesEnum.DAMAGES),
                analysis_config_data.get_analysis(
                    analysis_config_data.adaptation.losses_analysis
                ),
            )
            # First option is the no adaptation option
            if i == 0:
                _collection.no_adaptation_option = _option
                continue
            _collection.adaptation_options.append(_option)

        return _collection
