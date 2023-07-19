import pytest
import pandas as pd
import geopandas as gpd
from pathlib import Path
from ra2ce.analyses.indirect.traffic_analysis.equity_analysis import EquityAnalysis
from ra2ce.analyses.indirect.traffic_analysis.traffic_analysis import TrafficAnalysis
from ra2ce.analyses.indirect.traffic_analysis.traffic_analysis_base import (
    TrafficAnalysisBase,
)
from ra2ce.analyses.indirect.traffic_analysis.traffic_analysis_factory import (
    TrafficAnalysisFactory,
)

from tests import test_data, test_results
from tests.analyses.indirect.traffic_analysis.test_equity_analysis import (
    import_from_csv,
)


class TestTrafficAnalysisFactory:
    @pytest.mark.parametrize(
        "file_arg",
        [
            pytest.param("", id="Empty string"),
            pytest.param(None, id="No value given"),
            pytest.param(
                Path("does_not_exist.geojson"), id="Non-existing geojson file"
            ),
        ],
    )
    def test_read_equity_weights_without_file(self, file_arg: Path):
        # 1. Run test.
        _result = TrafficAnalysisFactory.read_equity_weights(file_arg)

        # 2. Verify expectations.
        assert isinstance(_result, pd.DataFrame)
        assert _result.empty

    @pytest.mark.parametrize("separator", [pytest.param(","), pytest.param(";")])
    def test_read_equity_weights_with_different_separator(
        self, separator: str, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        test_file = test_results.joinpath(
            request.node.originalname, "equity_example.csv"
        )
        if test_file.exists():
            test_file.unlink()
        test_file.parent.mkdir(parents=True, exist_ok=True)
        _test_data = pd.DataFrame.from_dict(
            {"a_column": [42, 24], "b_column": [4.2, 2.4]}
        )
        _test_data.to_csv(test_file, sep=separator, index=False)

        # 2. Run test.
        _result_dataframe = TrafficAnalysisFactory.read_equity_weights(test_file)

        # 3. Verify expectations.
        pd.testing.assert_frame_equal(_test_data, _result_dataframe)

    @pytest.mark.parametrize(
        "equity_data_value",
        [
            pytest.param(None, id="None as equity_data"),
            pytest.param(pd.DataFrame(), id="Empty DataFrame"),
        ],
    )
    def test_get_analysis_with_no_equity_data_returns_traffic_analysis(
        self, equity_data_value: pd.DataFrame
    ):
        # 1. Define test data.
        _gdf = gpd.GeoDataFrame()
        _od_table = gpd.GeoDataFrame()
        _destination_names = ""

        # 2. Run test.
        _result = TrafficAnalysisFactory.get_analysis(
            _gdf, _od_table, _destination_names, equity_data_value
        )

        # 3. Verify expectations.
        assert isinstance(_result, TrafficAnalysisBase)
        assert isinstance(_result, TrafficAnalysis)

    def test_get_analysis_with_equity_data_returns_equity_analysis(self):
        # 1. Define test data.
        _equity_test_data = test_data.joinpath("equity_data")
        _gdf_data = import_from_csv(_equity_test_data.joinpath("gdf_data.csv"))
        _od_table_data = import_from_csv(
            _equity_test_data.joinpath("od_table_data.csv")
        )
        _equity_data = pd.read_csv(_equity_test_data.joinpath("equity_data.csv"))
        _destination_names = ""
        assert "values_prioritarian" not in _od_table_data.columns

        # 2. Run test.
        _result = TrafficAnalysisFactory.get_analysis(
            _gdf_data, _od_table_data, _destination_names, _equity_data
        )

        # 3. Verify expectations.
        assert isinstance(_result, TrafficAnalysisBase)
        assert isinstance(_result, EquityAnalysis)
        pd.testing.assert_frame_equal(_result.gdf, _gdf_data)
        pd.testing.assert_frame_equal(_result.od_table, _od_table_data)
        pd.testing.assert_frame_equal(_result.equity_data, _equity_data)
        assert "values_prioritarian" in _od_table_data.columns
