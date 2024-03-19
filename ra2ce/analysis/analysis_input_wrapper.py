from pathlib import Path
from typing import Optional

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionBase
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.network.graph_files.graph_files_protocol import GraphFileProtocol
from ra2ce.network.hazard.hazard_names import HazardNames
from ra2ce.network.network_config_data.network_config_data import (
    OriginsDestinationsSection,
)


class AnalysisInputWrapper:
    analysis: AnalysisSectionBase
    graph_file: GraphFileProtocol
    graph_file_hazard: GraphFileProtocol
    input_path: Path
    static_path: Path
    output_path: Path
    hazard_names: Optional[HazardNames]
    origins_destinations: Optional[OriginsDestinationsSection]
    file_id: str

    def __init__(
        self, analysis: AnalysisSectionBase, analysis_config: AnalysisConfigWrapper
    ):
        self.analysis = analysis
        self.input_path = analysis_config.config_data.input_path
        self.static_path = analysis_config.config_data.static_path
        self.output_path = analysis_config.config_data.output_path
        self.hazard_names = HazardNames.from_config(analysis_config)
        self.origins_destinations = analysis_config.config_data.origins_destinations
        self.file_id = analysis_config.config_data.network.file_id
