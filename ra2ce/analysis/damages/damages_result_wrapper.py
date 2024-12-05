from attr import dataclass

from ra2ce.analysis.analysis_result.analysis_result import AnalysisResult
from ra2ce.analysis.analysis_result.analysis_result_wrapper_.protocol import (
    AnalysisResultWrapperProtocol,
)


@dataclass(kw_only=True)
class DamagesResultWrapper(AnalysisResultWrapperProtocol):
    segment_based_result: AnalysisResult
    link_based_result: AnalysisResult

    @property
    def results_collection(self) -> list[AnalysisResult]:
        return [self.segment_based_result, self.link_based_result]
