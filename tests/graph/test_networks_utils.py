import pytest

from ra2ce.graph.networks_utils import convert_unit, drawProgressBar


class TestNetworkUtils:
    @pytest.mark.parametrize(
        "unit_name, expected_value",
        [
            pytest.param("centimeters", 1 / 100, id="cm"),
            pytest.param("meters", 1, id="m"),
            pytest.param("feet", 1 / 3.28084, id="ft"),
        ],
    )
    def test_convert_unit(self, unit_name: str, expected_value: float):
        assert convert_unit(unit_name) == expected_value

    @pytest.mark.parametrize("percent", [(-20), (0), (50), (100), (150)])
    def test_draw_progress_bar(self, percent: float):
        drawProgressBar(percent)
