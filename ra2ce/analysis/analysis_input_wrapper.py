from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.network.graph_files.graph_files_protocol import GraphFileProtocol
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.network_config_data import (
    OriginsDestinationsSection,
)


@dataclass
class AnalysisInputWrapper:
    analysis: AnalysisConfigData.ANALYSIS_SECTION
    graph_file: Optional[GraphFileProtocol]
    graph_file_hazard: Optional[GraphFileProtocol]
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: Optional[HazardNames]
    origins_destinations: Optional[OriginsDestinationsSection]
    file_id: Optional[str]

    @classmethod
    def from_input(
        cls,
        analysis: AnalysisConfigData.ANALYSIS_SECTION,
        analysis_config: AnalysisConfigWrapper,
        graph_file: Optional[GraphFileProtocol] = None,
        graph_file_hazard: Optional[GraphFileProtocol] = None,
    ) -> AnalysisInputWrapper:
        return cls(
            analysis=analysis,
            graph_file=graph_file,
            graph_file_hazard=graph_file_hazard,
            input_path=analysis_config.config_data.input_path,
            static_path=analysis_config.config_data.static_path,
            output_path=analysis_config.config_data.output_path,
            hazard_names=HazardNames.from_config(analysis_config),
            origins_destinations=analysis_config.config_data.origins_destinations,
            file_id=analysis_config.config_data.network.file_id,
        )
