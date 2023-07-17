from pathlib import Path
from ra2ce.analyses.indirect.equity_analysis import EquityAnalysis
from tests import test_data, slow_test
import pytest
import geopandas as gpd
import pandas as pd

_equity_test_data = test_data.joinpath("equity_data")


def import_from_csv(input_file: Path) -> gpd.GeoDataFrame:
    assert input_file.exists()
    _as_pandas_df = pd.read_csv(input_file)
    _as_geo_df = gpd.GeoDataFrame(
        _as_pandas_df.loc[:, [c for c in _as_pandas_df.columns if c != "geometry"]],
        geometry=gpd.GeoSeries.from_wkt(_as_pandas_df["geometry"]),
        crs="epsg:3005",
    )
    assert isinstance(_as_geo_df, gpd.GeoDataFrame)
    return _as_geo_df


class TestEquityAnalysis:
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
        _result = EquityAnalysis.read_equity_weights(file_arg)

        # 2. Verify expectations.
        assert isinstance(_result, pd.DataFrame)
        assert _result.empty

    @slow_test
    def test_analysis_with_valid_data(self):
        # 1. Define test data.
        _destinations_names = "B"
        _gdf_data = import_from_csv(_equity_test_data.joinpath("gdf_data.csv"))
        _od_table_data = import_from_csv(
            _equity_test_data.joinpath("od_table_data.csv")
        )
        _equity_data = pd.read_csv(_equity_test_data.joinpath("equity_data.csv"))
        assert isinstance(_equity_data, pd.DataFrame)

        _expected_columns = [
            "u",
            "v",
            "traffic",
            "traffic_egalitarian",
            "traffic_prioritarian",
        ]

        # 2. Run test.
        _result = EquityAnalysis().optimal_route_od_link(
            _gdf_data, _od_table_data, _equity_data, _destinations_names
        )

        # 3. Verify expectations.
        assert isinstance(_result, pd.DataFrame)
        assert list(_result.columns).sort() == _expected_columns.sort()
