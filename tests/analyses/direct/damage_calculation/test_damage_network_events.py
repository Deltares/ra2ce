import pytest

from ra2ce.analyses.direct.damage_calculation.damage_network_base import (
    DamageNetworkBase,
)
from ra2ce.analyses.direct.damage_calculation.damage_network_events import (
    DamageNetworkEvents,
)


class TestDamageNetworkEvents:
    def test_init_with_valid_args(self):
        # 1. Define test data.
        _road_gf = None
        _val_cols = ["an_event_01", "an_event_02"]

        # 2. Run test
        _dne = DamageNetworkEvents(_road_gf, _val_cols)

        # 3. Verify final expectations
        assert isinstance(_dne, DamageNetworkEvents)
        assert isinstance(_dne, DamageNetworkBase)
        assert list(_dne.events) == ["event"]

    def test_init_with_invalid_args(self):
        # 1. Define test data.
        _road_gf = None
        _val_cols = []

        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            DamageNetworkEvents(_road_gf, _val_cols)

        # 3. Verify final expectations.
        assert str(exc_err.value) == "No event cols present in hazard data"
