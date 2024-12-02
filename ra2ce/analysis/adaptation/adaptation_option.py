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

from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptationOption,
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)


@dataclass
class AdaptationOption:
    id: str
    name: str
    construction_cost: float
    construction_interval: float
    maintenance_cost: float
    maintenance_interval: float
    damages_config: AnalysisSectionDamages
    losses_config: AnalysisSectionLosses

    @classmethod
    def from_config(
        cls,
        adaptation_option: AnalysisSectionAdaptationOption,
        damages_section: AnalysisSectionDamages,
        losses_section: AnalysisSectionLosses,
    ) -> AdaptationOption:
        # Adjust path to the input files
        def extend_path(analysis: str, input_path: Path | None) -> Path | None:
            if not input_path:
                return None
            return input_path.parent.joinpath(
                "input", adaptation_option.id, analysis, input_path.name
            )

        if not damages_section or not losses_section:
            raise ValueError(
                "Damages and losses sections are required to create an adaptation option."
            )

        _damages_section = deepcopy(damages_section)

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
            **asdict(adaptation_option),
            damages_config=_damages_section,
            losses_config=_losses_section,
        )

    def calculate_cost(self, time_horizon: float, discount_rate: float) -> float:
        """
        Calculate the net present value unit cost (per meter) of the adaptation option.

        Args:
            time_horizon (float): The total time horizon of the analysis.
            discount_rate (float): The discount rate to apply to the costs.

        Returns:
            float: The net present value unit cost of the adaptation option.
        """

        def calc_years(from_year: float, to_year: float, interval: float) -> range:
            return range(
                round(from_year),
                round(min(to_year, time_horizon)),
                round(interval),
            )

        def calc_cost(cost: float, year: float) -> float:
            return cost * (1 - discount_rate) ** year

        _constr_years = calc_years(
            0,
            time_horizon,
            self.construction_interval,
        )
        _lifetime_cost = 0.0
        for _constr_year in _constr_years:
            # Calculate the present value of the construction cost
            _lifetime_cost += calc_cost(self.construction_cost, _constr_year)

            # Calculate the present value of the maintenance cost
            _maint_years = calc_years(
                _constr_year + self.maintenance_interval,
                _constr_year + self.construction_interval,
                self.maintenance_interval,
            )
            for _maint_year in _maint_years:
                _lifetime_cost += calc_cost(self.maintenance_cost, _maint_year)

        return _lifetime_cost
