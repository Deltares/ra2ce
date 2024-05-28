import json

import pandas as pd
import pytest

from tests import test_data

_analysis_direct_data = test_data / "analysis_direct_damages"


@pytest.fixture
def gdf_test_direct_damage() -> pd.DataFrame:
    _json_file = _analysis_direct_data / "gdf_direct_damage.json"
    assert _json_file.exists()
    return pd.DataFrame.from_dict(json.loads(_json_file.read_text()))


@pytest.fixture
def gdf_test_direct_damage_correct() -> pd.DataFrame:
    _json_file = _analysis_direct_data / "gdf_direct_damage_correct.json"
    assert _json_file.exists()
    return pd.DataFrame.from_dict(json.loads(_json_file.read_text()))
