import pytest
from geopandas import GeoDataFrame
from shapely import Point

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.analysis_result.analysis_result import AnalysisResult
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper


class TestAnalysisBase:
    def test_initialize(self):
        # 1. Define test.
        _analysis_base = AnalysisBase()

        # 2. Verify expectations
        assert isinstance(_analysis_base, AnalysisBase)

    def test_generate_result_wrapper_single_result(
        self, mocked_analysis: AnalysisProtocol
    ):
        # 1. Define test data.
        _result_gfd = GeoDataFrame(
            {
                "dummy_column": ["left", "right"],
                "geometry": [Point(4.2, 2.4), Point(42, 24)],
            }
        )
        _analysis_base = AnalysisBase()
        _analysis_base.analysis = mocked_analysis.analysis
        _analysis_base.output_path = mocked_analysis.output_path

        # 2. Run test.
        _result_wrapper = _analysis_base.generate_result_wrapper(_result_gfd)

        # 3. Verify expectations.
        assert isinstance(_result_wrapper, AnalysisResultWrapper)
        assert len(_result_wrapper.results_collection) == 1
        _single_result = _result_wrapper.get_single_analysis()
        assert isinstance(_single_result, AnalysisResult)
        assert _single_result.analysis_result.equals(_result_gfd)
        assert _single_result.analysis_config == mocked_analysis.analysis
