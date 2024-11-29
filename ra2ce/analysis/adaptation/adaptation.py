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
from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.adaptation.adaptation_option_collection import (
    AdaptationOptionCollection,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionAdaptation,
)
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.network.graph_files.network_file import NetworkFile


class Adaptation(AnalysisDamagesProtocol):
    analysis: AnalysisSectionAdaptation
    graph_file: NetworkFile
    graph_file_hazard: NetworkFile
    input_path: Path
    output_path: Path
    _adaptation_options: AdaptationOptionCollection

    # TODO: add the proper protocol for the adaptation analysis.
    def __init__(
        self, analysis_input: AnalysisInputWrapper, analysis_config: AnalysisConfigData
    ):
        self.analysis_input = analysis_input
        self._adaptation_options = AdaptationOptionCollection.from_config(
            analysis_config
        )

    def execute(self) -> GeoDataFrame | None:
        """
        Run the adaptation analysis.
        """
        return self.calculate_bc_ratio()

    def calculate_option_cost(self, option: AdaptationOption) -> float:
        def calc_years(from_year: float, to_year: float, interval: float) -> range:
            return range(
                round(from_year),
                round(min(to_year, self._adaptation_options.time_horizon)),
                round(interval),
            )

        def calc_cost(cost: float, year: float) -> float:
            return cost * (1 - self._adaptation_options.discount_rate) ** year

        _constr_years = calc_years(
            0,
            self._adaptation_options.time_horizon,
            option.construction_interval,
        )
        _lifetime_cost = 0.0
        for _constr_year in _constr_years:
            # Calculate the present value of the construction cost
            _lifetime_cost += calc_cost(option.construction_cost, _constr_year)

            # Calculate the present value of the maintenance cost
            _maint_years = calc_years(
                _constr_year + option.maintenance_interval,
                _constr_year + option.construction_interval,
                option.maintenance_interval,
            )
            for _maint_year in _maint_years:
                _lifetime_cost += calc_cost(option.maintenance_cost, _maint_year)

        return _lifetime_cost

    def run_cost(self) -> GeoDataFrame | None:
        """
        Calculate the cost of the adaptation.
        """
        return 0.0

    def run_benefit(self) -> GeoDataFrame | None:
        """
        Calculate the benefit of the adaptation.
        """
        return 0.0

    def calculate_bc_ratio(self) -> GeoDataFrame | None:
        """
        Calculate the benefit-cost ratio of the adaptation.
        """
        self.run_cost()
        self.run_benefit()
        return 0.0
