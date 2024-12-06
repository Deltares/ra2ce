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

from dataclasses import asdict, dataclass

from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation_option_analysis import (
    AdaptationOptionAnalysis,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptationOption,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper


@dataclass
class AdaptationOption:
    id: str
    name: str
    construction_cost: float
    construction_interval: float
    maintenance_cost: float
    maintenance_interval: float
    analyses: list[AdaptationOptionAnalysis]
    analysis_config: AnalysisConfigWrapper

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def from_config(
        cls,
        analysis_config: AnalysisConfigWrapper,
        adaptation_option: AnalysisSectionAdaptationOption,
    ) -> AdaptationOption:
        """
        Classmethod to create an AdaptationOption from an analysis configuration and an adaptation option.

        Args:
            analysis_config (AnalysisConfigWrapper): Analysis config input
            adaptation_option (AnalysisSectionAdaptationOption): Adaptation option input

        Raises:
            ValueError: If damages and losses sections are not present in the analysis config data.

        Returns:
            AdaptationOption: The created adaptation option.
        """
        if (
            not analysis_config.config_data.damages_list
            or not analysis_config.config_data.losses_list
        ):
            raise ValueError(
                "Damages and losses sections are required to create an adaptation option."
            )

        # Create input for the analyses
        _analyses = [
            AdaptationOptionAnalysis.from_config(
                analysis_config=analysis_config,
                analysis_type=_analysis,
                option_id=adaptation_option.id,
            )
            for _analysis in [
                AnalysisDamagesEnum.DAMAGES,
                analysis_config.config_data.adaptation.losses_analysis,
            ]
        ]

        return cls(
            **asdict(adaptation_option),
            analyses=_analyses,
            analysis_config=analysis_config,
        )

    def calculate_unit_cost(self, time_horizon: float, discount_rate: float) -> float:
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

    def calculate_impact(
        self, benefit_graph: GeoDataFrame, net_present_value_factor: float
    ) -> GeoDataFrame:
        """
        Calculate the impact of the adaptation option.

        Returns:
            float: The impact of the adaptation option.
        """
        for _analysis in self.analyses:
            _result = _analysis.execute(self.analysis_config)
            _col = _result.filter(regex=_analysis.result_col).columns[0]
            benefit_graph[f"{self.id}_{_col}"] = _result[_col]

        # Calculate the impact (summing the damages and losses values)
        _option_cols = benefit_graph.filter(regex=f"{self.id}_").columns
        benefit_graph[f"{self.id}_impact"] = benefit_graph[_option_cols].sum(axis=1)

        # convert event impact into time-horizon impact
        benefit_graph[f"{self.id}_impact"] = (
            benefit_graph[f"{self.id}_impact"] * net_present_value_factor
        )

        return benefit_graph
