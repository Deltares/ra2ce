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
    all_options: list[AdaptationOption] = field(default_factory=list)

    @property
    def reference_option(self) -> AdaptationOption:
        if not self.all_options:
            return None
        return self.all_options[0]

    @property
    def adaptation_options(self) -> list[AdaptationOption]:
        if len(self.all_options) < 2:
            return []
        return self.all_options[1:]

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

        _damages_analysis = analysis_config_data.get_analysis(
            AnalysisDamagesEnum.DAMAGES
        )
        _losses_analysis = analysis_config_data.get_analysis(
            analysis_config_data.adaptation.losses_analysis
        )
        for _config_option in analysis_config_data.adaptation.adaptation_options:
            _collection.all_options.append(
                AdaptationOption.from_config(
                    analysis_config_data.root_path,
                    _config_option,
                    _damages_analysis,
                    _losses_analysis,
                )
            )

        return _collection

    def calculate_option_cost(self) -> dict[AdaptationOption, float]:
        """
        Calculate the cost for all adaptation options.
        """
        return {
            _option: _option.calculate_cost(
                self.time_horizon,
                self.discount_rate,
            )
            for _option in self.adaptation_options
        }
