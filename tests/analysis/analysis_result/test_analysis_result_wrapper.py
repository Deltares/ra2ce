from typing import Callable

import pytest
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_result.analysis_result_wrapper import (
    AnalysisResult,
    AnalysisResultWrapper,
)


class TestAnalysisResultWrapper:
    def test_initialize(self):
        # 1. Define test data.
        _results_collection = []

        # 2. Run test.
        _result_wrapper = AnalysisResultWrapper(results_collection=_results_collection)

        # 3. Verify expectations.
        assert isinstance(_result_wrapper, AnalysisResultWrapper)

    @pytest.mark.parametrize(
        "invalid_geodataframe",
        [
            pytest.param(None, id="No GeoDataFrame provided"),
            pytest.param(GeoDataFrame(), id="Empty GeoDataFrame"),
        ],
    )
    def test_given_invalid_result_when_is_valid_result_returns_false(
        self,
        invalid_geodataframe: GeoDataFrame,
        analysis_result_builder: Callable[[GeoDataFrame], AnalysisResult],
    ):
        # 1. Define test data.
        _result_wrapper = AnalysisResultWrapper(
            results_collection=[analysis_result_builder(invalid_geodataframe)]
        )

        # 2. Run test.
        _result = _result_wrapper.is_valid_result()

        # 3. Verify expectations.
        assert _result is False

    def test_given_valid_result_when_is_valid_result_returns_true(
        self, analysis_result_builder: Callable[[GeoDataFrame], AnalysisResult]
    ):
        # 1. Define test data.
        _geo_dataframe = GeoDataFrame.from_dict(dict(dummy=[(4.2, 2.4), (42, 24)]))
        _result_wrapper = AnalysisResultWrapper(
            results_collection=[analysis_result_builder(_geo_dataframe)]
        )

        # 2. Run test.
        _result = _result_wrapper.is_valid_result()

        # 3. Verify expectations.
        assert _result is True
