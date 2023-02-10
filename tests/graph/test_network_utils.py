import pytest

from ra2ce.graph.networks_utils import convert_unit, drawProgressBar


class TestNetworkUtils:
    @pytest.mark.parametrize(
        "unit, expected_result",
        [
            pytest.param("centimeters", 1 / 100, id="cm"),
            pytest.param("meters", 1, id="m"),
            pytest.param("feet", 1 / 3.28084, id="ft"),
        ],
    )
    def test_convert_unit(self, unit: str, expected_result: float):
        assert convert_unit(unit) == expected_result

    @pytest.mark.parametrize("percent", [(-20), (0), (50), (100), (110)])
    def test_draw_progress_bar(self, percent: float):
        drawProgressBar(percent)
