from typing import Protocol, runtime_checkable

from ra2ce.analysis.analysis_result.analysis_result import AnalysisResult


@runtime_checkable
class AnalysisResultWrapperProtocol(Protocol):
    results_collection: list[AnalysisResult]

    def is_valid_result(self) -> bool:
        """
        Validates whether the `analyses_results` in this wrapper are all valid.

        Returns:
            bool: validation of `analyses_results`.
        """
