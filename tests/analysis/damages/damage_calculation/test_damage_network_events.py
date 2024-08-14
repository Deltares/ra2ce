import pandas as pd
import pytest

from ra2ce.analysis.damages.damage_calculation.damage_network_base import (
    DamageNetworkBase,
)
from ra2ce.analysis.damages.damage_calculation.damage_network_events import (
    DamageNetworkEvents,
)


class TestDamageNetworkEvents:
    def test_init_with_valid_args(self):
        # 1. Define test data.
        _road_gf = None
        _val_cols = ["an_event_01", "an_event_02"]
        _representative_damage_percentage = 100
        # 2. Run test
        _dne = DamageNetworkEvents(
            _road_gf, _val_cols, _representative_damage_percentage, "highway"
        )

        # 3. Verify final expectations
        assert isinstance(_dne, DamageNetworkEvents)
        assert isinstance(_dne, DamageNetworkBase)
        assert list(_dne.events) == ["event"]

    def test_init_with_invalid_args(self):
        # 1. Define test data.
        _road_gf = None
        _val_cols = []
        _representative_damage_percentage = 100

        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            _dne = DamageNetworkEvents(
                _road_gf, _val_cols, _representative_damage_percentage, "highway"
            )

        # 3. Verify final expectations.
        assert str(exc_err.value) == "No event cols present in hazard data"

    @pytest.mark.skip(reason="Results are not yet comparable (#319)")
    def test_damages_analysis_event_huizinga(
        self, road_gdf: pd.DataFrame, gdf_correct: pd.DataFrame
    ):
        assert isinstance(road_gdf, pd.DataFrame)
        assert isinstance(gdf_correct, pd.DataFrame)
        # Find the hazard columns
        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        event_gdf = DamageNetworkEvents(road_gdf, val_cols, 100, "highway")
        event_gdf.main(damage_function="HZ")

        test_outcomes = event_gdf.gdf

        test_outcomes.sort_values("osm_id")
        gdf_correct.sort_values("osm_id")

        test_outcomes.reset_index(inplace=True)
        gdf_correct.reset_index(inplace=True)

        assert pd.testing.assert_series_equal(
            test_outcomes["dam_EV1_HZ"],
            gdf_correct["dam_HZ_rp100"],
            check_dtype=False,
            check_index_type=False,
            check_series_type=False,
            check_names=False,
            check_exact=False,
        )
