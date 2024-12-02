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

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionAdaptationOption,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.damages.damages import Damages
from ra2ce.analysis.losses.multi_link_losses import MultiLinkLosses
from ra2ce.analysis.losses.single_link_losses import SingleLinkLosses


@dataclass
class AdaptationOption:
    id: str
    name: str
    construction_cost: float
    construction_interval: float
    maintenance_cost: float
    maintenance_interval: float
    damages_input: AnalysisInputWrapper
    losses_input: AnalysisInputWrapper
    losses_analysis: AnalysisLossesEnum
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
        Classmethod to create an adaptation option from an analysis configuration and an adaptation option.

        Args:
            analysis_config (AnalysisConfigWrapper): Analysis config input
            adaptation_option (AnalysisSectionAdaptationOption): Adaptation option input

        Raises:
            ValueError: If damages and losses sections are not present in the analysis config data.

        Returns:
            AdaptationOption: The created adaptation option.
        """
        # Adjust path to the files (should be in Adaptation/input)
        def construct_path(
            orig_path: Path,
            analysis: str,
            folder: str,
        ) -> Path:
            if not orig_path:
                return None
            # Orig is directory: add stuff at the end
            if not (orig_path.suffix):
                return orig_path.parent.joinpath(
                    "input", adaptation_option.id, analysis, folder
                )
            return orig_path.parent.parent.joinpath(
                "input", adaptation_option.id, analysis, folder, orig_path.name
            )

        def replace_paths(
            config_data: AnalysisConfigData, analysis: str
        ) -> AnalysisConfigData:
            config_data.input_path = construct_path(
                config_data.input_path, analysis, "input"
            )
            config_data.static_path = construct_path(
                config_data.static_path, analysis, "static"
            )
            config_data.output_path = construct_path(
                config_data.output_path, analysis, "output"
            )
            return config_data

        if (
            not analysis_config.config_data.damages_list
            or not analysis_config.config_data.losses_list
        ):
            raise ValueError(
                "Damages and losses sections are required to create an adaptation option."
            )

        # Create config for the damages analysis
        _damages_config = deepcopy(analysis_config)
        _damages_config.config_data = replace_paths(
            _damages_config.config_data, "damages"
        )
        _damages_analysis = _damages_config.config_data.get_analysis(
            AnalysisDamagesEnum.DAMAGES
        )
        _damages_input = AnalysisInputWrapper.from_input(
            analysis=_damages_analysis,
            analysis_config=_damages_config,
            graph_file_hazard=analysis_config.graph_files.base_network_hazard,
        )

        # Create config for the losses analysis
        _losses_config = deepcopy(analysis_config)
        _losses_config.config_data = replace_paths(_losses_config.config_data, "losses")
        _losses_analysis = _losses_config.config_data.get_analysis(
            analysis_config.config_data.adaptation.losses_analysis
        )
        _losses_analysis.traffic_intensities_file = construct_path(
            _losses_analysis.traffic_intensities_file, "losses", "input"
        )
        _losses_analysis.resilience_curves_file = construct_path(
            _losses_analysis.resilience_curves_file, "losses", "input"
        )
        _losses_analysis.values_of_time_file = construct_path(
            _losses_analysis.values_of_time_file, "losses", "input"
        )
        _losses_analysis
        _losses_input = AnalysisInputWrapper.from_input(
            analysis=_losses_analysis,
            analysis_config=_losses_config,
            graph_file=analysis_config.graph_files.base_graph,
            graph_file_hazard=analysis_config.graph_files.base_graph_hazard,
        )

        return cls(
            **asdict(adaptation_option),
            damages_input=_damages_input,
            losses_input=_losses_input,
            losses_analysis=analysis_config.config_data.adaptation.losses_analysis,
            analysis_config=analysis_config,
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

    def calculate_impact(self) -> GeoDataFrame:
        """
        Calculate the impact of the adaptation option.

        Returns:
            float: The impact of the adaptation option.
        """
        _damages = Damages(self.damages_input)
        _damages_gdf = _damages.execute()

        if self.losses_analysis is AnalysisLossesEnum.SINGLE_LINK_LOSSES:
            _losses = SingleLinkLosses(self.losses_input, self.analysis_config)
        elif self.losses_analysis is AnalysisLossesEnum.MULTI_LINK_LOSSES:
            _losses = MultiLinkLosses(self.losses_input, self.analysis_config)
        else:
            raise NotImplementedError(
                f"Losses analysis {self.losses_analysis} not implemented"
            )
        _losses_gdf = _losses.execute()

        return _damages_gdf
