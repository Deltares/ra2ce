from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

from tests import test_data

_equity_test_data = test_data.joinpath("equity_data")


@dataclass
class TrafficAnalysisInput:
    destinations_name: str
    road_network: gpd.GeoDataFrame
    od_table_data: gpd.GeoDataFrame
    equity_data: pd.DataFrame


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


@pytest.fixture
def valid_traffic_analysis_input() -> TrafficAnalysisInput:
    yield TrafficAnalysisInput(
        destinations_name="B",
        road_network=import_from_csv(_equity_test_data.joinpath("gdf_data.csv")),
        od_table_data=import_from_csv(_equity_test_data.joinpath("od_table_data.csv")),
        equity_data=pd.read_csv(_equity_test_data.joinpath("equity_data.csv")),
    )
