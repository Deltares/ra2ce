from dataclasses import dataclass
import geopandas as gpd
from ra2ce.analysis.analysis_result_protocol import AnalysisResultProtocol
from ra2ce.network.graph_files.graph_files_protocol import GraphFileProtocol
from ra2ce.network.graph_files.network_file import NetworkFile


@dataclass
class DirectAnalysisResultWrapper(AnalysisResultProtocol):

    analysis_result: gpd.GeoDataFrame
    network_file: NetworkFile

    def is_valid_result(self) -> bool:
        return self.analysis_result and not self.analysis_result.empty


@dataclass
class IndirectAnalysisResultWrapper(AnalysisResultProtocol):

    analysis_result: gpd.GeoDataFrame
    graph_file: GraphFileProtocol

    def is_valid_result(self) -> bool:
        return self.analysis_result and not self.analysis_result.empty
