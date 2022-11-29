# -*- coding: utf-8 -*-
import pandas as pd
import pytest

from ra2ce.analyses.direct.damage.manual_damage_functions import ManualDamageFunctions
from ra2ce.analyses.direct.direct_damage_calculation import (
    DamageNetworkEvents,
    DamageNetworkReturnPeriods,
)


class TestDirectAnalyses:
    @pytest.mark.skip(reason="Results are not yet comparable")
    def test_direct_analysis_event_huizinga(self):
        from tests.test_data.direct_analyses_data.direct_analyses_data import (
            gdf_test_direct_damage,
            gdf_test_direct_damage_correct,
        )

        road_gdf = pd.DataFrame.from_dict(gdf_test_direct_damage)
        gdf_correct = pd.DataFrame.from_dict(gdf_test_direct_damage_correct)

        # Find the hazard columns
        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        event_gdf = DamageNetworkEvents(road_gdf, val_cols)
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
