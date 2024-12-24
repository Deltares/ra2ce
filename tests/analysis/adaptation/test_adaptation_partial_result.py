import pytest
from geopandas import GeoDataFrame
from pandas import Series
from shapely import Point

from ra2ce.analysis.adaptation.adaptation_option_analysis import (
    AdaptationOptionAnalysis,
)
from ra2ce.analysis.adaptation.adaptation_partial_result import AdaptationPartialResult
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)


class TestAdaptationPartialResult:
    def test_initialize(self):
        # 1./2. Define test data./Run test.
        _result = AdaptationPartialResult(None, None)

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationPartialResult)
        assert isinstance(_result.data_frame, GeoDataFrame)

    @pytest.mark.parametrize(
        "analysis_type, col_name, match",
        [
            pytest.param(
                AnalysisDamagesEnum.DAMAGES, "dam_EV1_al", True, id="valid damages"
            ),
            pytest.param(
                AnalysisDamagesEnum.DAMAGES,
                "dam_EV1_al_segments",
                False,
                id="invalid damages",
            ),
            pytest.param(
                AnalysisLossesEnum.SINGLE_LINK_LOSSES,
                "vlh_EV1_me_total",
                True,
                id="valid losses",
            ),
            pytest.param(
                AnalysisLossesEnum.SINGLE_LINK_LOSSES,
                "vlh_business_EV1_me",
                False,
                id="invalid losses",
            ),
        ],
    )
    def test_from_gdf_with_matched_col_returns_object(
        self,
        analysis_type: AnalysisDamagesEnum | AnalysisLossesEnum,
        col_name: str,
        match: bool,
    ):
        # 1. Define test data.
        _id_col = "link_id"
        _gdf = GeoDataFrame.from_dict(
            {_id_col: range(10), "geometry": Point(1, 0), col_name: range(10)}
        )
        _result_col = AdaptationOptionAnalysis.get_analysis_info(analysis_type)[2]

        # 2. Run test.
        _result = AdaptationPartialResult.from_gdf_with_matched_col(
            _gdf, _id_col, _result_col, analysis_type
        )

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationPartialResult)
        assert analysis_type.config_value in _result.data_frame.columns
        assert (
            _result.data_frame[analysis_type.config_value].sum() == pytest.approx(45)
        ) == match

    def test_merge_partial_results_with_unequal_column_length(self):
        # 1. Define test data.
        _this_nof_rows = 10
        _this_result_col = "this_result"
        _this_result = AdaptationPartialResult(
            id_col="this_link_id",
            data_frame=GeoDataFrame.from_dict(
                {
                    "this_link_id": range(_this_nof_rows),
                    "geometry": [Point(x, 0) for x in range(_this_nof_rows)],
                    _this_result_col: range(_this_nof_rows),
                }
            ),
        )
        _other_nof_rows = 8
        _other_result_col = "other_result"
        _other_result = AdaptationPartialResult(
            id_col="other_link_id",
            data_frame=GeoDataFrame.from_dict(
                {
                    "other_link_id": reversed(range(_other_nof_rows)),
                    "geometry": [Point(x, 0) for x in range(_other_nof_rows)],
                    _other_result_col: range(0, 2 * _other_nof_rows, 2),
                }
            ),
        )

        # 2. Run test.
        _this_result.merge_partial_results(_other_result)

        # 3. Verify expectations.
        assert isinstance(_this_result, AdaptationPartialResult)
        assert all(
            _col in _this_result.data_frame.columns
            for _col in [_this_result_col, _other_result_col]
        )
        assert _this_result.data_frame.shape[0] == _this_nof_rows
        assert _this_result.data_frame[_this_result_col].sum() == pytest.approx(45)
        assert _this_result.data_frame[_other_result_col].sum() == pytest.approx(56)

    def test_add_option_id(self):
        # 1. Define test data.
        _result_col1 = "result1"
        _result_col2 = "result2"
        _partial_result = AdaptationPartialResult(
            id_col="link_id",
            data_frame=GeoDataFrame.from_dict(
                {
                    "link_id": range(10),
                    "geometry": [Point(x, 0) for x in range(10)],
                    _result_col1: range(10),
                    _result_col2: range(0, 20, 2),
                }
            ),
        )
        _option_id = "Option1"

        # 2. Run test.
        _partial_result.add_option_id(_option_id)

        # 3. Verify expectations.
        assert isinstance(_partial_result, AdaptationPartialResult)
        assert all(
            f"{_option_id}_{_col}" in _partial_result.data_frame.columns
            for _col in [_result_col1, _result_col2]
        )
        assert all(
            not _col in _partial_result.data_frame.columns
            for _col in [_result_col1, _result_col2]
        )

    def test_put_option_column(self):
        # 1. Define test data.
        _partial_result = AdaptationPartialResult(
            id_col="link_id",
            data_frame=GeoDataFrame.from_dict(
                {
                    "link_id": range(10),
                    "geometry": [Point(x, 0) for x in range(10)],
                    "result1": range(10),
                }
            ),
        )
        _option_id = "Option1"
        _col_type = "cost"
        _data = Series(range(10), name="result2")

        # 2. Run test.
        _partial_result.put_option_column(_option_id, _col_type, _data)

        # 3. Verify expectations.
        assert isinstance(_partial_result, AdaptationPartialResult)
        assert f"{_option_id}_{_col_type}" in _partial_result.data_frame.columns
        assert _partial_result.data_frame[
            f"{_option_id}_{_col_type}"
        ].sum() == pytest.approx(45)

    def test_get_option_column(self):
        # 1. Define test data.
        _option_id = "Option1"
        _col_type = "cost"
        _partial_result = AdaptationPartialResult(
            id_col="link_id",
            data_frame=GeoDataFrame.from_dict(
                {
                    "link_id": range(10),
                    "geometry": [Point(x, 0) for x in range(10)],
                    f"{_option_id}_{_col_type}": range(10),
                }
            ),
        )

        # 2. Run test.
        _result = _partial_result.get_option_column(_option_id, _col_type)

        # 3. Verify expectations.
        assert isinstance(_result, Series)
        assert sum(_result) == pytest.approx(45)
