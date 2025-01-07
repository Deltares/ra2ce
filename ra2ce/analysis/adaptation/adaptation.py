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

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.damages.analysis_damages_protocol import AnalysisDamagesProtocol
from ra2ce.network.graph_files.network_file import NetworkFile


class Adaptation(AnalysisBase, AnalysisDamagesProtocol):
    """
    Execute the adaptation analysis.
    For each adaptation option a damages and/or losses analysis is executed.
    """

    analysis: AnalysisSectionAdaptation
    graph_file_hazard: NetworkFile
    input_path: Path
    output_path: Path
    all_options: list[AdaptationOption]

    def __init__(
        self,
        analysis_input: AnalysisInputWrapper,
        analysis_config: AnalysisConfigWrapper,
    ):
        self.analysis = analysis_input.analysis
        self.graph_file_hazard = analysis_input.graph_file_hazard
        self.input_path = analysis_input.input_path
        self.output_path = analysis_input.output_path

        self.all_options = [
            AdaptationOption.from_config(
                analysis_config,
                _config_option,
            )
            for _config_option in analysis_config.config_data.adaptation.adaptation_options
        ]

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

    def execute(self) -> AnalysisResultWrapper:
        """
        Run the adaptation analysis.
        This is done by calculating the impact of the reference option first.
        Then the BC-ratio of the adaptation options is calculated.
        The reference and option results are combined in a single result.

        Returns:
            AnalysisResultWrapper: The result of the adaptation analysis.
        """
        _reference_impact = self.reference_option.get_impact()

        _result_gdf = _reference_impact.data_frame.copy()
        for _option in self.adaptation_options:
            _option_result = _option.get_bc_ratio(
                _reference_impact,
                self.graph_file_hazard.get_graph(),
                self.analysis.hazard_fraction_cost,
            )
            # Copy the option result columns.
            if _option_result != _reference_impact:
                raise ValueError("The results don't contain the same link_ids.")
            for _col in _option_result.result_cols:
                _result_gdf[_col] = _option_result.data_frame[_col]

        return self.generate_result_wrapper(_result_gdf)
