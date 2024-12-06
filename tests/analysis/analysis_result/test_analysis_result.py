import pytest
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_result.analysis_result import AnalysisResult


class TestAnalysisResult:
    def test_initialize(self):
        # 1. Define test data.
        _analysis_result = None
        _analysis_config = None
        _output_path = None

        # 2. Run test.
        _result = AnalysisResult(
            analysis_result=_analysis_result,
            analysis_config=_analysis_config,
            output_path=_output_path,
        )

        # 3. Verify expectations.
        assert isinstance(_result, AnalysisResult)
        assert _result.analysis_result is None
        assert _result.analysis_config is None
        assert _result.output_path is None
        assert _result.analysis_name == ""

    @pytest.mark.parametrize(
        "invalid_geodataframe",
        [
            pytest.param(None, id="No GeoDataFrame provided"),
            pytest.param(GeoDataFrame(), id="Empty GeoDataFrame"),
        ],
    )
    def test_given_invalid_result_when_is_valid_result_returns_false(
        self, invalid_geodataframe: GeoDataFrame
    ):
        # 1. Define test data.
        _result_wrapper = AnalysisResult(
            analysis_result=invalid_geodataframe, analysis_config=None, output_path=None
        )

        # 2. Run test.
        _result = _result_wrapper.is_valid_result()

        # 3. Verify expectations.
        assert _result is False

    def test_given_valid_result_when_is_valid_result_returns_true(self):
        # 1. Define test data.
        _geo_dataframe = GeoDataFrame.from_dict(dict(dummy=[(4.2, 2.4), (42, 24)]))
        _result_wrapper = AnalysisResult(
            analysis_result=_geo_dataframe, analysis_config=None, output_path=None
        )

        # 2. Run test.
        _result = _result_wrapper.is_valid_result()

        # 3. Verify expectations.
        assert _result is True
