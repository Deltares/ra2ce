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

import numpy as np
from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper


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
        analysis_config: AnalysisConfigWrapper,
    ) -> AdaptationOptionCollection:
        """
        Classmethod to create a collection of adaptation options from an analysis configuration.

        Args:
            analysis_config (AnalysisConfigWrapper): Analysis config input

        Raises:
            ValueError: If no adaptation section is found in the analysis config data.

        Returns:
            AdaptationOptionCollection: The created collection of adaptation options.
        """
        if (
            analysis_config.config_data is None
            or analysis_config.config_data.adaptation is None
        ):
            raise ValueError("No adaptation section found in the analysis config data.")

        _collection = cls(
            discount_rate=analysis_config.config_data.adaptation.discount_rate,
            time_horizon=analysis_config.config_data.adaptation.time_horizon,
            climate_factor=analysis_config.config_data.adaptation.climate_factor,
            initial_frequency=analysis_config.config_data.adaptation.initial_frequency,
        )
        for _config_option in analysis_config.config_data.adaptation.adaptation_options:
            _collection.all_options.append(
                AdaptationOption.from_config(
                    analysis_config,
                    _config_option,
                )
            )

        return _collection

    def get_net_present_value_factor(self) -> float:
        """
        Calculate the net present value factor for the entire time horizon. To be multiplied to the event impact to
        obtain the net present value.
        """
        _years_array = np.arange(0, self.time_horizon)
        _frequency_per_year = (
            self.initial_frequency + _years_array * self.climate_factor
        )
        _discount = (1 + self.discount_rate) ** _years_array
        _ratio = _frequency_per_year / _discount
        return _ratio.sum()

    def calculate_options_unit_cost(self) -> dict[AdaptationOption, float]:
        """
        Calculate the unit cost for all adaptation options.

        Returns:
            dict[AdaptationOption, float]: The calculated cost for all adaptation options.
        """
        return {
            _option: _option.calculate_unit_cost(
                self.time_horizon,
                self.discount_rate,
            )
            for _option in self.adaptation_options
        }

    def calculate_options_benefit(self) -> GeoDataFrame:
        """
        Calculate the benefit of all adaptation options.
        The benefit is calculated by subtracting the impact of the reference option from the impact of the adaptation option.

        Returns:
            GeoDataFrame: The calculated impact of all adaptation options.
        """
        net_present_value_factor = self.get_net_present_value_factor()
        _benefit_gdf = GeoDataFrame()

        # Calculate impact of reference option
        _impact_gdf = self.reference_option.calculate_impact(net_present_value_factor)
        for _col in _impact_gdf.columns:
            _benefit_gdf[_col] = _impact_gdf[_col]

        # Calculate impact and benefit of adaptation options
        for _option in self.adaptation_options:
            _impact_gdf = _option.calculate_impact(net_present_value_factor)
            for _col in _impact_gdf.columns:
                _benefit_gdf[_col] = _impact_gdf[_col]
            _benefit_gdf[_option.benefit_col] = (
                _benefit_gdf[_option.impact_col]
                - _benefit_gdf[self.reference_option.impact_col]
            )

        return _benefit_gdf
