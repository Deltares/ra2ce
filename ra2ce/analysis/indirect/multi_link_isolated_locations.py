from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect,
)
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.hazard.hazard_names import HazardNames


class MultiLinkIsolatedLocations(AnalysisIndirectProtocol):
    graph_file: GraphFile
    analysis: AnalysisSectionIndirect
    input_path: Path
    output_path: Path
    hazard_names: HazardNames
    result: GeoDataFrame

    def __init__(
        self,
        graph_file: GraphFile,
        analysis: AnalysisSectionIndirect,
        input_path: Path,
        output_path: Path,
        hazard_names: HazardNames,
    ) -> None:
        self.graph_file = graph_file
        self.analysis = analysis
        self.input_path = input_path
        self.output_path = output_path
        self.hazard_names = hazard_names
        self.result = None

    def execute(self) -> GeoDataFrame:
        pass
