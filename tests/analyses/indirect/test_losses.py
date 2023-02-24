import itertools

import numpy as np
import pandas as pd
import pytest

from ra2ce.analyses.indirect.losses import Losses


class TestLosses:
    def test_initialize(self):
        # 1. Define test data
        _config = {}
        _analyses = {
            "duration_event": None,
            "duration_disruption": None,
            "fraction_detour": None,
            "fraction_drivethrough": None,
            "rest_capacity": None,
            "maximum_jam": None,
            "partofday": None,
        }

        # 2. Run test.
        _losses = Losses(_config, _analyses)

        # 3. Verify final expectations.
        assert isinstance(_losses, Losses)

    def test_traffic_shockwave(self):
        # 1. Define test data
        _config = {}
        _analyses = {
            "duration_event": 60,
            "duration_disruption": None,
            "fraction_detour": None,
            "fraction_drivethrough": 24,
            "rest_capacity": 42,
            "maximum_jam": None,
            "partofday": None,
        }
        _losses = Losses(_config, _analyses)
        _capacity = pd.Series([42, 24, 12])
        _intensity = pd.Series([4.2, 2.4, 1.2])
        _vlh = pd.DataFrame()

        # 2. Run test.
        _result = _losses.traffic_shockwave(_vlh, _capacity, _intensity)

        # 3. Verify expectations
        assert _result.equals(_vlh)
        assert "vlh_traffic" in _vlh
        assert _vlh["vlh_traffic"].values == pytest.approx(
            [1.307149e08, 7.46942460e07, 3.73471230e07]
        )

    @pytest.mark.parametrize(
        "part_of_day", [pytest.param("daily"), pytest.param("evening")]
    )
    def test_calc_vlh(self, part_of_day: str):
        # 1. Define test data
        # TODO: Not sure of the input format values float of series?
        _config = {}
        _analyses = {
            "duration_event": 60,
            "duration_disruption": 15,
            "fraction_detour": 1.24,
            "fraction_drivethrough": 24,
            "rest_capacity": 42,
            "maximum_jam": 100,
            "partofday": part_of_day,
        }
        _losses = Losses(_config, _analyses)
        _traffic_data = pd.DataFrame(
            {
                "capacity": [10, 5, 2],
                "day_total": [100, 50, 20],
                "day_freight": [30, 60, 90],
                "day_commute": [30, 60, 90],
                "day_business": [30, 60, 90],
                "day_other": [30, 60, 90],
                "evening_total": [50, 25, 10],
                "evening_freight": [15, 30, 60],
                "evening_commute": [15, 30, 60],
                "evening_business": [15, 30, 60],
                "evening_other": [15, 30, 60],
            }
        )
        _mi = list(
            itertools.product(
                ["freight", "commute", "business", "other"], ["vehicle_loss_hour"]
            )
        )
        _mi_idx = pd.MultiIndex.from_tuples(_mi, names=["A", "B"])
        _vehicle_loss_hours = pd.Series(np.random.randn(4), index=_mi_idx)
        _detour_data = pd.DataFrame(
            {
                "detour_time_day": [30, 20, 10],
                "detour_time_evening": [15, 10, 5],
            }
        )

        # 2. Run test.
        _result = _losses.calc_vlh(_traffic_data, _vehicle_loss_hours, _detour_data)

        # 3. Verify final expectations.
        assert isinstance(_result, pd.DataFrame)
        assert "euro_per_hour" in _result
        assert "euro_vlh" in _result
        assert "vlh_total" in _result
        assert "vlh_traffic" in _result
        assert "vlh_detour" in _result
