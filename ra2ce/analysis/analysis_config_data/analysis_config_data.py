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
from pathlib import Path
from typing import Optional

from ra2ce.analysis.analysis_config_data.adaptation_config_data import (
    AdaptationConfigData,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.base_rootable_paths import BaseRootablePaths
from ra2ce.analysis.analysis_config_data.damages_config_data import DamagesConfigData
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_data.losses_analysis_config_data_protocol import (
    BaseLossesAnalysisConfigData,
)
from ra2ce.common.configuration.config_data_protocol import ConfigDataProtocol
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.network_config_data import (
    NetworkSection,
    OriginsDestinationsSection,
)


@dataclass
class ProjectSection:
    """
    Reflects all possible settings that a project section might contain.
    """

    name: str = ""


@dataclass
class AnalysisConfigData(ConfigDataProtocol):
    """
    Represents all configuration data for analyses in RA2CE, including defaults from analysis.ini.

    This class consolidates analysis configuration settings and integrates relevant network attributes
    (e.g., network, origins/destinations, hazard names) for convenience.

    Attributes
    ----------
    ANALYSIS_SECTION
        Union type for analysis sections (damages, losses, adaptation).

    root_path
        Root directory path for the project.

    input_path
        Input directory path for the project.

    output_path
        Output directory path where results will be saved.

    static_path
        Path to static project files.

    project
        Section containing project metadata.

    analyses
        List of all analysis to run consecutively.

    origins_destinations
        Section containing origins and destinations data.

    network
        Section containing network configuration data.


    """

    root_path: Optional[Path] = None
    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    static_path: Optional[Path] = None
    project: ProjectSection = field(default_factory=ProjectSection)
    analyses: list[AnalysisConfigDataProtocol] = field(default_factory=list)
    origins_destinations: Optional[OriginsDestinationsSection] = field(
        default_factory=OriginsDestinationsSection
    )
    network: NetworkSection = field(default_factory=NetworkSection)
    aggregate_wl: AggregateWlEnum = field(default_factory=lambda: AggregateWlEnum.NONE)

    def reroot_analysis_config(
        self,
        analysis_type: AnalysisConfigDataProtocol,
        new_root: Path,
    ) -> AnalysisConfigData:
        """
        Reroot dependent analysis in config data to the input of another analysis.

        Returns:
            AnalysisConfigData: The rerooted config data.
        """

        _analysis = self.get_analysis(analysis_type)
        
        def reroot_path(orig_path: Optional[Path]) -> Optional[Path]:
            # Rewrite the path to the new root
            if not orig_path or not self.root_path:
                return None
            _orig_parts = orig_path.parts
            _rel_path = Path(*_orig_parts[len(self.root_path.parts) :])
            return new_root.joinpath(_analysis.config_name, _rel_path)

        self.input_path = reroot_path(self.input_path)

        # Rewrite the paths of the input files in the analysis config
        if isinstance(_analysis, BaseRootablePaths):
            _analysis.reroot_fields(self.root_path, new_root)

        self.root_path = new_root

        return self

    @property
    def damages_list(self) -> list[DamagesConfigData]:
        """
        Get all damages analyses from config.

        Returns:
            list[DamagesConfigData]: List of all damages analyses.
        """
        return list(
            filter(lambda x: isinstance(x, DamagesConfigData), self.analyses)
        )

    @property
    def losses_list(self) -> list[BaseLossesAnalysisConfigData]:
        """
        Get all losses analyses from config.

        Returns:
            list[LossesAnalysisConfigDataProtocol]: List of all losses analyses.
        """
        return list(
            filter(lambda x: isinstance(x, BaseLossesAnalysisConfigData), self.analyses)
        )

    @property
    def adaptation(self) -> AdaptationConfigData | None:
        """
        Get the adaptation analysis from config.

        Returns:
            AdaptationConfigData: Adaptation analysis.
        """
        return next(
            filter(lambda x: isinstance(x, AdaptationConfigData), self.analyses),
            None,
        )

    def get_analysis(
        self, analysis_type: type[AnalysisConfigDataProtocol]
    ) -> AnalysisConfigDataProtocol | None:
        """
        Get a certain analysis from config.

        Returns:
            AnalysisConfigDataProtocol: The analysis.
        """
        return next(filter(lambda x: isinstance(x, analysis_type), self.analyses), None)

    @staticmethod
    def get_data_output(ini_file: Path) -> Path:
        return ini_file.parent.joinpath("output")
