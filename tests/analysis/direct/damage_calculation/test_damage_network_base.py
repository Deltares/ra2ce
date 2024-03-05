import geopandas as gpd
import numpy as np
import pytest

from ra2ce.analyses.direct.damage_calculation.damage_network_base import (
    DamageNetworkBase,
)


class MockedDNB(DamageNetworkBase):
    """
    Mocked class to emulate what would happen if the abstract methods would not be implemented by the inheriting classes.
    """

    def main(self, damage_function: str, manual_damage_functions):
        return super().main(damage_function, manual_damage_functions)


class TestDamageNetworkBase:
    def test_init_network_base_raises(self):
        with pytest.raises(TypeError):
            DamageNetworkBase(None, [])

    def test_main_raises_error(self):
        # 1. Define test data.
        _dnb = MockedDNB(None, [])

        # 2. Run test
        with pytest.raises(ValueError) as exc_err:
            _dnb.main("", None)

        # 3. Verify final expectations.
        assert str(exc_err.value) == "Needs to be implented in concrete child class."

    def test_create_mask(self):
        # 1. Define test data.
        _dnb = MockedDNB(None, [])
        _dnb.gdf = gpd.GeoDataFrame.from_dict({"geometry": [None, None]})
        _dnb.val_cols = ["_fr"]
        assert "geometry" in _dnb.gdf.columns

        # 2. Run test
        _dnb.create_mask()

        # 3. Verify expectations
        assert "geometry" not in _dnb._gdf_mask.columns

    def test_replace_none_with_nan(self):
        # 1. Define test data.
        _dnb = MockedDNB(None, [])
        _dnb.gdf = gpd.GeoDataFrame.from_dict(
            {"dam_abc": [None, None], "dam_cde": [None, None]}
        )

        # 2. Run test
        _dnb.replace_none_with_nan()

        # 3. Verify final expectations
        assert len(_dnb.gdf["dam_abc"].values) == 2
        assert all(np.isnan(v) for v in _dnb.gdf["dam_abc"].values)
        assert len(_dnb.gdf["dam_cde"].values) == 2
        assert all(np.isnan(v) for v in _dnb.gdf["dam_cde"].values)
