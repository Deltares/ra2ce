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

    @property
    def cost_col(self) -> str:
        return self._get_column_name("cost")

    @property
    def impact_col(self) -> str:
        return self._get_column_name("impact")

    @property
    def benefit_col(self) -> str:
        return self._get_column_name("benefit")

    @property
    def bc_ratio_col(self) -> str:
        return self._get_column_name("bc_ratio")

    def _get_column_name(self, col_type: str) -> str:
        return f"{self.id}_{col_type}"

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
            and not analysis_config.config_data.losses_list
        ):
            raise ValueError(
                "Damages and/or losses sections are required to create an adaptation option."
            )

        # Create input for the damages and losses analyses (if present in config)
        _config_analyses = [x.analysis for x in analysis_config.config_data.analyses]
        _analyses = [
            AdaptationOptionAnalysis.from_config(
                analysis_config=analysis_config,
                analysis_type=_analysis_type,
                option_id=adaptation_option.id,
            )
            for _analysis_type in [
                AnalysisDamagesEnum.DAMAGES,
                analysis_config.config_data.adaptation.losses_analysis,
            ]
            if _analysis_type in _config_analyses
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

    def calculate_impact(self, net_present_value_factor: float) -> GeoDataFrame:
        """
        Calculate the impact of the adaptation option.

        Returns:
            GeoDataFrame: The impact of the adaptation option.
        """
        _result_gdf = GeoDataFrame()
        for _analysis in self.analyses:
            _result_gdf[
                f"{self.impact_col}_{_analysis.analysis_type.config_value}"
            ] = _analysis.execute(self.analysis_config)

        # Calculate the impact (summing the results of the analyses)
        _result_gdf[self.impact_col] = (
            _result_gdf.sum(axis=1) * net_present_value_factor
        )

        return _result_gdf
