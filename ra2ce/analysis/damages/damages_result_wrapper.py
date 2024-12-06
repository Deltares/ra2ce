from attr import dataclass

from ra2ce.analysis.analysis_result.analysis_result import AnalysisResult
from ra2ce.analysis.analysis_result.analysis_result_wrapper_protocol import (
    AnalysisResultWrapperProtocol,
)


@dataclass(kw_only=True)
class DamagesResultWrapper(AnalysisResultWrapperProtocol):
    segment_based_result: AnalysisResult
    link_based_result: AnalysisResult

    @property
    def results_collection(self) -> list[AnalysisResult]:
        return [self.segment_based_result, self.link_based_result]

    def is_valid_result(self):
        return any(self.results_collection) and all(
            map(AnalysisResult.is_valid_result, self.results_collection)
        )
