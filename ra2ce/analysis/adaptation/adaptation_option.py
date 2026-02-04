"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023-2026 Stichting Deltares

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
from dataclasses import asdict, dataclass

from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation_option_analysis import (
    AdaptationOptionAnalysis,
)
from ra2ce.analysis.adaptation.adaptation_option_partial_result import (
    AdaptationOptionPartialResult,
)
from ra2ce.analysis.adaptation.adaptation_result_enum import AdaptationResultEnum
from ra2ce.analysis.adaptation.adaptation_settings import AdaptationSettings
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
    adaptation_settings: AdaptationSettings

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
                analysis_config,
                _analysis_type,
                adaptation_option.id,
            )
            for _analysis_type in [
                AnalysisDamagesEnum.DAMAGES,
                analysis_config.config_data.adaptation.losses_analysis,
            ]
            if _analysis_type in _config_analyses
        ]

        _adaptation_settings = AdaptationSettings(
            discount_rate=analysis_config.config_data.adaptation.discount_rate,
            time_horizon=analysis_config.config_data.adaptation.time_horizon,
            initial_frequency=analysis_config.config_data.adaptation.initial_frequency,
            climate_factor=analysis_config.config_data.adaptation.climate_factor,
        )

        return cls(
            **asdict(adaptation_option),
            analyses=_analyses,
            analysis_config=analysis_config,
            adaptation_settings=_adaptation_settings,
        )

    def get_bc_ratio(
        self,
        reference_impact: AdaptationOptionPartialResult,
        gdf_in: GeoDataFrame,
        hazard_fraction_cost: bool,
    ) -> AdaptationOptionPartialResult:
        """
        Calculate the benefit-cost ratio of the adaptation option.

        Args:
            reference_impact (AdaptationOptionPartialResult): The impact of the reference option.

        Returns:
            AdaptationOptionPartialResult: The benefit-cost ratio of the adaptation option.
        """
        # Calculate cost
        _result = self._get_cost(gdf_in, hazard_fraction_cost)

        # Calculate impact/benefit
        _result += self._get_benefit(reference_impact)

        # Calculate BC-ratio
        _benefit = _result.get_column(AdaptationResultEnum.BENEFIT)
        _cost = _result.get_column(AdaptationResultEnum.COST)

        _result.add_column(
            AdaptationResultEnum.BC_RATIO,
            _benefit / _cost.replace(0, math.nan),
        )
        return _result

    def _get_benefit(
        self, reference_impact: AdaptationOptionPartialResult
    ) -> AdaptationOptionPartialResult:
        _result = self.get_impact()

        # Benefit = reference impact - adaptation impact
        _benefit = reference_impact.get_column(
            AdaptationResultEnum.NET_IMPACT
        ) - _result.get_column(AdaptationResultEnum.NET_IMPACT)
        _result.add_column(AdaptationResultEnum.BENEFIT, _benefit)

        return _result

    def _get_cost(
        self, gdf_in: GeoDataFrame, hazard_fraction_cost: bool
    ) -> AdaptationOptionPartialResult:
        """
        Calculate the cost of the adaptation option.

        Args:
            input_gdf (GeoDataFrame): The input GeoDataFrame.

        Returns:
            AdaptationOptionPartialResult: The cost of the adaptation option.
        """
        _result = AdaptationOptionPartialResult.from_input_gdf(self.id, gdf_in)
        _cost_col = gdf_in.apply(
            lambda x, cost=self._get_unit_cost(): x["length"] * cost, axis=1
        )

        # Only calculate the cost for the impacted fraction of the links.
        if hazard_fraction_cost:
            _fraction_col = gdf_in.filter(regex="EV.*_fr").columns[0]
            _cost_col *= gdf_in[_fraction_col]

        _result.add_column(AdaptationResultEnum.COST, _cost_col)

        return _result

    def _get_unit_cost(self) -> float:
        """
        Calculate the net present value unit cost (per meter) of the adaptation option.

        Args:
            None

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
            return _cost / (1 + self.adaptation_settings.discount_rate) ** year

        return sum(
            calculate_cost(_year)
            for _year in range(0, round(self.adaptation_settings.time_horizon), 1)
        )

    def get_impact(self) -> AdaptationOptionPartialResult:
        """
        Calculate the impact of the adaptation option.

        Args:
            net_present_value_factor (float): The net present value factor to apply to the event impact.

        Returns:
            AdaptationOptionPartialResult: The impact (event and net) of the adaptation option per link.
        """
        # Get all results from the analyses
        _result = AdaptationOptionPartialResult(option_id=self.id)
        for _analysis in self.analyses:
            _result += _analysis.execute(self.analysis_config)

        # Calculate the impact (summing the results of the analysis results per link)
        _impact = _result.data_frame.filter(regex=self.id).sum(axis=1)
        _result.add_column(AdaptationResultEnum.EVENT_IMPACT, _impact)
        _result.add_column(
            AdaptationResultEnum.NET_IMPACT,
            _impact * self.adaptation_settings.net_present_value_factor,
        )

        return _result
