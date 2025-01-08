import pytest
from geopandas import GeoDataFrame
from pandas import Series
from shapely import Point

from ra2ce.analysis.adaptation.adaptation_option_analysis import (
    AdaptationOptionAnalysis,
)
from ra2ce.analysis.adaptation.adaptation_option_partial_result import (
    AdaptationOptionPartialResult,
)
from ra2ce.analysis.adaptation.adaptation_result_enum import AdaptationResultEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)


class TestAdaptationOptionPartialResult:
    def test_initialize_with_minimal_input(self):
        # 1./2. Define test data./Run test.
        _option_id = "Option1"
        _result = AdaptationOptionPartialResult(_option_id)

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOptionPartialResult)
        assert _result.option_id == _option_id
        assert isinstance(_result.data_frame, GeoDataFrame)

    def test_initialize_with_full_input(self):
        # 1. Define test data.
        _option_id = "Option1"
        _id_col = "rfid"
        _gdf = GeoDataFrame.from_dict(
            {_id_col: range(10), "geometry": [Point(x, 0) for x in range(10)]}
        )

        # 2. Run test.
        _result = AdaptationOptionPartialResult(option_id=_option_id, data_frame=_gdf)

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOptionPartialResult)
        assert _result.option_id == _option_id
        assert _result._id_col == _id_col
        assert _result.data_frame.shape[0] == 10
        assert _id_col in _result.data_frame.columns
        assert "geometry" in _result.data_frame.columns

    def test_from_input_gdf_returns_object(self):
        # 1. Define test data.
        _option_id = "Option1"
        _gdf_in = GeoDataFrame.from_dict(
            {"rfid": range(10), "geometry": [Point(x, 0) for x in range(10)]}
        )

        # 2. Run test.
        _result = AdaptationOptionPartialResult.from_input_gdf(_option_id, _gdf_in)

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationOptionPartialResult)
        assert _result.option_id == _option_id
        assert _result.data_frame.shape[0] == 10

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
        _option_id = "Option1"
        _id_col = "rfid"
        _gdf = GeoDataFrame.from_dict(
            {_id_col: range(10), "geometry": Point(1, 0), col_name: range(10)}
        )
        _result_col = AdaptationOptionAnalysis.get_analysis_info(analysis_type)[1]

        # 2. Run test.
        _result = AdaptationOptionPartialResult.from_gdf_with_matched_col(
            _option_id, _gdf, _result_col, analysis_type
        )

        # 3. Verify expectations.
        _result_col = f"{_option_id}_{analysis_type.config_value}"
        assert isinstance(_result, AdaptationOptionPartialResult)
        assert _result_col in _result.data_frame.columns
        assert (_result.data_frame[_result_col].sum() == pytest.approx(45)) == match

    def test_add_partial_results_with_unequal_column_length(self):
        # 1. Define test data.
        _option_id = "Option1"
        _id_col = "rfid"
        _this_nof_rows = 10
        _this_result_col = "this_result"
        _this_result = AdaptationOptionPartialResult(
            option_id=_option_id,
            data_frame=GeoDataFrame.from_dict(
                {
                    _id_col: range(_this_nof_rows),
                    "geometry": [Point(x, 0) for x in range(_this_nof_rows)],
                    _this_result_col: range(_this_nof_rows),
                }
            ),
        )
        _other_nof_rows = 8
        _other_result_col = "other_result"
        _other_result = AdaptationOptionPartialResult(
            option_id=_option_id,
            data_frame=GeoDataFrame.from_dict(
                {
                    _id_col: reversed(range(_other_nof_rows)),
                    "geometry": [Point(x, 0) for x in range(_other_nof_rows)],
                    _other_result_col: range(0, 2 * _other_nof_rows, 2),
                }
            ),
        )

        # 2. Run test.
        _this_result += _other_result

        # 3. Verify expectations.
        assert isinstance(_this_result, AdaptationOptionPartialResult)
        assert all(
            _col in _this_result.data_frame.columns
            for _col in [_this_result_col, _other_result_col]
        )
        assert _this_result.data_frame.shape[0] == _this_nof_rows
        assert _this_result.data_frame[_this_result_col].sum() == pytest.approx(45)
        assert _this_result.data_frame[_other_result_col].sum() == pytest.approx(56)

    def test_add_partial_results_with_other_key_order(self):
        # 1. Define test data.
        _option_id = "Option1"
        _id_col = "rfid"
        _custom_id = [5, 6, 7, 8, 9, 0, 1, 2, 3, 4]
        _this_result = AdaptationOptionPartialResult(
            option_id=_option_id,
            data_frame=GeoDataFrame.from_dict(
                {
                    _id_col: _custom_id,
                    "Result1": [i + 1 for i in _custom_id],
                }
            ),
        )
        _other_result = AdaptationOptionPartialResult(
            option_id=_option_id,
            data_frame=GeoDataFrame.from_dict(
                {
                    _id_col: list(reversed(_custom_id)),
                    "Result2": [i + 1 for i in reversed(_custom_id)],
                }
            ),
        )
        assert not any(
            _other_result.data_frame["Result2"] == _this_result.data_frame["Result1"]
        )

        # 2. Run test.
        _this_result += _other_result

        # 3. Verify expectations.
        assert all(
            _this_result.data_frame["Result2"] == _this_result.data_frame["Result1"]
        )

    def test_add_partial_results_with_different_option_ids_raises(self):
        # 1. Define test data.
        _id_col = "rfid"
        _this_result = AdaptationOptionPartialResult(
            option_id="Option1",
            data_frame=GeoDataFrame.from_dict({_id_col: range(10)}),
        )
        _other_result = AdaptationOptionPartialResult(
            option_id="Option2",
            data_frame=GeoDataFrame.from_dict({_id_col: range(10)}),
        )

        # 2. Run test.
        with pytest.raises(ValueError) as exc:
            _this_result += _other_result

        # 3. Verify expectations.
        assert exc.match(
            "Cannot merge partial results from different adaptation options."
        )

    def test_put_option_column(self):
        # 1. Define test data.
        _option_id = "Option1"
        _partial_result = AdaptationOptionPartialResult(
            option_id=_option_id,
            data_frame=GeoDataFrame.from_dict(
                {
                    "rfid": range(10),
                    "geometry": [Point(x, 0) for x in range(10)],
                    "result1": range(10),
                }
            ),
        )
        _col_type = AdaptationResultEnum.COST
        _data = Series(range(10), name="result2")

        # 2. Run test.
        _partial_result.add_column(_col_type, _data)

        # 3. Verify expectations.
        _result_col = f"{_option_id}_{_col_type.config_value}"
        assert isinstance(_partial_result, AdaptationOptionPartialResult)
        assert _result_col in _partial_result.data_frame.columns
        assert _partial_result.data_frame[_result_col].sum() == pytest.approx(45)

    def test_get_option_column(self):
        # 1. Define test data.
        _option_id = "Option1"
        _col_type = AdaptationResultEnum.COST
        _partial_result = AdaptationOptionPartialResult(
            option_id=_option_id,
            data_frame=GeoDataFrame.from_dict(
                {
                    "rfid": range(10),
                    "geometry": [Point(x, 0) for x in range(10)],
                    f"{_option_id}_{_col_type.config_value}": range(10),
                }
            ),
        )

        # 2. Run test.
        _result = _partial_result.get_column(_col_type)

        # 3. Verify expectations.
        assert isinstance(_result, Series)
        assert sum(_result) == pytest.approx(45)
