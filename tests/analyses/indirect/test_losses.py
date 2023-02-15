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
