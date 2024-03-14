from dataclasses import dataclass
import geopandas as gpd
from ra2ce.analysis.analysis_result_protocol import AnalysisResultProtocol
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
from ra2ce.analysis.indirect.analysis_indirect_protocol import AnalysisIndirectProtocol


@dataclass
class DirectAnalysisResultWrapper(AnalysisResultProtocol):

    analysis_result: gpd.GeoDataFrame
    analysis: AnalysisDirectProtocol

    def is_valid_result(self) -> bool:
        return self.analysis_result and not self.analysis_result.empty


@dataclass
class IndirectAnalysisResultWrapper(AnalysisResultProtocol):

    analysis_result: gpd.GeoDataFrame
    analysis: AnalysisIndirectProtocol

    def is_valid_result(self) -> bool:
        return self.analysis_result and not self.analysis_result.empty
