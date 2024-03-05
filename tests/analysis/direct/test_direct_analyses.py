# -*- coding: utf-8 -*-
import pandas as pd
import pytest

from ra2ce.analyses.direct.damage_calculation import DamageNetworkEvents


class TestDirectAnalyses:
    @pytest.mark.skip(reason="Results are not yet comparable")
    def test_direct_analysis_event_huizinga(
        self, road_gdf: pd.DataFrame, gdf_correct: pd.DataFrame
    ):
        assert isinstance(road_gdf, pd.DataFrame)
        assert isinstance(gdf_correct, pd.DataFrame)
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
