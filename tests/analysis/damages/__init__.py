import json

import pandas as pd
import pytest

from tests import test_data

_analysis_damages_data = test_data / "analysis_damages"


@pytest.fixture
def gdf_test_damages() -> pd.DataFrame:
    _json_file = _analysis_damages_data / "gdf_damages.json"
    assert _json_file.exists()
    return pd.DataFrame.from_dict(json.loads(_json_file.read_text()))


@pytest.fixture
def gdf_test_damages_correct() -> pd.DataFrame:
    _json_file = _analysis_damages_data / "gdf_damages_correct.json"
    assert _json_file.exists()
    return pd.DataFrame.from_dict(json.loads(_json_file.read_text()))
