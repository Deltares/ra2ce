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

        def is_constr_year(year: float) -> bool:
            if self.construction_interval == 0:
                return False
            return (round(year) % round(self.construction_interval)) == 0

        def is_maint_year(year: float) -> bool:
            if self.maintenance_interval == 0:
                return False
            if self.construction_interval > 0:
                # Take year relative to last construction year
                year = round(year) % round(self.construction_interval)
            return (year % round(self.maintenance_interval)) == 0

        def calculate_cost(year) -> float:
            if is_constr_year(year):
                _cost = self.construction_cost
            elif is_maint_year(year):
                _cost = self.maintenance_cost
            else:
                return 0.0
            return _cost / (1 + discount_rate) ** year

        return sum(calculate_cost(_year) for _year in range(0, round(time_horizon), 1))

    def calculate_impact(
        self, benefit_graph: GeoDataFrame, net_present_value_factor: float
    ) -> GeoDataFrame:
        """
        Calculate the impact of the adaptation option.

        Returns:
            float: The impact of the adaptation option.
        """
        for _analysis in self.analyses:
            _result_wrapper = _analysis.execute(self.analysis_config)
            # Assumes a single result.
            _analysis_result = _result_wrapper.results_collection[0].analysis_result
            _col = _analysis_result.filter(regex=_analysis.result_col).columns[0]
            benefit_graph[f"{self.id}_{_col}"] = _analysis_result[_col]

        # Calculate the impact (summing the damages and losses values)
        _option_cols = benefit_graph.filter(regex=f"{self.id}_").columns
        benefit_graph[f"{self.id}_impact"] = benefit_graph[_option_cols].sum(axis=1)

        # convert event impact into time-horizon impact
        benefit_graph[f"{self.id}_impact"] *= net_present_value_factor

        return benefit_graph
