import numpy as np
import pandas as pd
import pytest

from ra2ce.analyses.direct.damage_calculation.damage_network_base import (
    DamageNetworkBase,
)
from ra2ce.analyses.direct.damage_calculation.damage_network_return_periods import (
    DamageNetworkReturnPeriods,
)


class TestDamageNetworkReturnPeriods:
    def test_init(self):
        # 1. Define test data.
        _road_gf = None
        _val_cols = ["an_event_ab", "an_event_cd"]

        # 2. Run test.
        _damage = DamageNetworkReturnPeriods(_road_gf, _val_cols)

        # 2. Verify expectations.
        assert isinstance(_damage, DamageNetworkReturnPeriods)
        assert isinstance(_damage, DamageNetworkBase)
        assert list(_damage.return_periods) == ["event"]

    def test_init_with_no_event_raises_error(self):
        # 1. Define test data.
        _road_gf = None
        _val_cols = []

        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            DamageNetworkReturnPeriods(_road_gf, _val_cols)

        # 3. Verify expectations
        assert str(exc_err.value) == "No return_period cols present in hazard data"

    @pytest.mark.skip(
        reason="TODO: Too many required arguments. Better to test with real data."
    )
    @pytest.mark.parametrize(
        "damage_function",
        [pytest.param("HZ"), pytest.param("OSD"), pytest.param("MAN")],
    )
    def test_main_with_valid_data(self, damage_function: str):
        # 1. Define test data.
        _road_gf = None
        _val_cols = ["an_me", "an_fr"]
        _damage = DamageNetworkReturnPeriods(_road_gf, _val_cols)
        _manual_functions = None
        # 2. Run test.
        _damage.main(damage_function, _manual_functions)

        # 3. Verify expectations.

    def test_integrate_df_trapezoidal(self):
        # 1. Define test data.
        data = np.array(([[1000, 2000], [500, 1000]]))
        rps = [100, 200]
        df = pd.DataFrame(data, columns=rps)

        # 2. Run test.
        res = DamageNetworkReturnPeriods.integrate_df_trapezoidal(df)

        # 3. Verify expectations.
        assert np.array_equal(res, np.array([7.5, 3.75]))
