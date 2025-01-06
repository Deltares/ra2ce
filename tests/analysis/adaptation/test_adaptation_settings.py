import pytest

from ra2ce.analysis.adaptation.adaptation_settings import AdaptationSettings


class TestAdaptationSettings:
    def test_net_present_value_factor(self):
        # 1. Define test data
        _settings = AdaptationSettings(
            discount_rate=0.025,
            time_horizon=20,
            initial_frequency=0.01,
            climate_factor=0.0001,
        )

        # 2. Run test
        _result = _settings.net_present_value_factor

        # 3. Verify expectations
        assert isinstance(_result, float)
        assert _result == pytest.approx(0.1736623)
