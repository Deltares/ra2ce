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
from dataclasses import dataclass
from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionLosses,
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
from ra2ce.analysis.losses.losses_base import LossesBase
from ra2ce.analysis.losses.multi_link_losses import MultiLinkLosses
from ra2ce.analysis.losses.single_link_losses import SingleLinkLosses


@dataclass
class AdaptationOptionAnalysis:
    analysis_type: type[Damages | LossesBase]
    analysis_input: AnalysisInputWrapper
    result_col: str

    @staticmethod
    def get_analysis(
        analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum,
    ) -> tuple[type[Damages | LossesBase], str]:
        """
        Get the analysis type and the result column for the given analysis.

        Args:
            analysis (AnalysisDamagesEnum | AnalysisLossesEnum): The type of analysis.

        Raises:
            NotImplementedError: The analysis type is not implemented.

        Returns:
            tuple[type[Damages | LossesBase], str]: The analysis type and the result column.
        """
        if analysis_type == AnalysisDamagesEnum.DAMAGES:
            return (Damages, "dam_")
        elif analysis_type == AnalysisLossesEnum.SINGLE_LINK_LOSSES:
            return (SingleLinkLosses, "vlh_.*_total")
        elif analysis_type == AnalysisLossesEnum.MULTI_LINK_LOSSES:
            return (MultiLinkLosses, "vlh_.*_total")
        raise NotImplementedError(f"Analysis {analysis_type} not implemented")

    @classmethod
    def from_config(
        cls,
        analysis_config: AnalysisConfigWrapper,
        analysis: AnalysisLossesEnum | AnalysisDamagesEnum,
        option_id: str,
    ) -> AdaptationOptionAnalysis:
        """
        Classmethod to create an AdaptationOptionAnalysis from an analysis configuration.

        Args:
            analysis_config (AnalysisConfigWrapper): The analysis configuration.
            analysis (AnalysisLossesEnum | AnalysisDamagesEnum): The type of analysis.
            option_id (str): The ID of the adaptation option.

        Returns:
            AdaptationOptionAnalysis: The created AdaptationOptionAnalysis.
        """

        def construct_path(
            orig_path: Path,
            folder: str,
        ) -> Path:
            # Adjust path to the files (should be in Adaptation/input)
            if not orig_path:
                return None
            # Orig is directory: add stuff at the end
            if not (orig_path.suffix):
                return orig_path.parent.joinpath(
                    "input", option_id, analysis.config_value, folder
                )
            return orig_path.parent.parent.joinpath(
                "input", option_id, analysis.config_value, folder, orig_path.name
            )

        def replace_paths(config_data: AnalysisConfigData) -> AnalysisConfigData:
            # Replace paths in the config data
            config_data.input_path = construct_path(config_data.input_path, "input")
            config_data.static_path = construct_path(config_data.static_path, "static")
            config_data.output_path = construct_path(config_data.output_path, "output")
            return config_data

        # Need a deepcopy to avoid mixing up configs across analyses.
        _analysis_config = deepcopy(analysis_config)

        # Replace all paths in the config data to point to the nested options folder.
        _analysis_config.config_data = replace_paths(_analysis_config.config_data)
        _analysis_data = _analysis_config.config_data.get_analysis(analysis)
        if isinstance(_analysis_data, AnalysisSectionLosses):
            _analysis_data.traffic_intensities_file = construct_path(
                _analysis_data.traffic_intensities_file, "input"
            )
            _analysis_data.resilience_curves_file = construct_path(
                _analysis_data.resilience_curves_file, "input"
            )
            _analysis_data.values_of_time_file = construct_path(
                _analysis_data.values_of_time_file, "input"
            )

        if analysis == AnalysisDamagesEnum.DAMAGES:
            _graph_file = None
            _graph_file_hazard = analysis_config.graph_files.base_network_hazard
        else:
            _graph_file = analysis_config.graph_files.base_graph
            _graph_file_hazard = analysis_config.graph_files.base_graph_hazard

        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=_analysis_data,
            analysis_config=_analysis_config,
            graph_file=_graph_file,
            graph_file_hazard=_graph_file_hazard,
        )

        _analysis_type, _result_col = cls.get_analysis(analysis)

        return cls(
            analysis_type=_analysis_type,
            analysis_input=_analysis_input,
            result_col=_result_col,
        )

    def execute(self, analysis_config: AnalysisConfigWrapper) -> GeoDataFrame:
        """
        Execute the analysis.

        Args:
            analysis_config (AnalysisConfigWrapper): The config for the analysis.

        Returns:
            DataFrame: The results of the analysis.
        """
        if self.analysis_type == Damages:
            return self.analysis_type(self.analysis_input).execute()
        return self.analysis_type(self.analysis_input, analysis_config).execute()
