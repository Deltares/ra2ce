from abc import ABC

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper


class AnalysisBase(ABC, AnalysisProtocol):
    """
    Abstract class to help extend common functionality among the analysis implementing
    the `AnalysisProtocol`.
    """

    def generate_result_wrapper(
        self, analysis_result: GeoDataFrame
    ) -> AnalysisResultWrapper:
        """
        Creates a result wrapper based on a given `GeoDataFrame` result for
        the calling analysis (`AnalysisProtocol`).

        Args:
            analysis_result (GeoDataFrame): Resulting dataframe of an analysis.

        Returns:
            AnalysisResultWrapper: Wrapping result with configuration details.
        """
        return AnalysisResultWrapper(
            analysis_result=analysis_result,
            analysis_config=self.analysis,
            output_path=self.output_path,
        )
