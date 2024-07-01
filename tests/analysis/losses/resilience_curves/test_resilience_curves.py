import pytest

from ra2ce.analysis.losses.resilience_curves.resilience_curves import ResilienceCurves
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class TestResilienceCurve:
    @pytest.fixture(name="valid_resilience_curves")
    def _get_valid_resilience_curves(
        self,
        resilience_curves_data: list[
            tuple[RoadTypeEnum, tuple[float, float], list[float], list[float]]
        ],
    ):
        _resilience_curves = ResilienceCurves()
        for _data in resilience_curves_data:
            _resilience_curves.link_type.append(_data[0])
            _resilience_curves.hazard_range.append(_data[1])
            _resilience_curves.duration_steps.append(_data[2])
            _resilience_curves.functionality_loss_ratio.append(_data[3])
        return _resilience_curves

    @pytest.mark.parametrize(
        "link_type, hazard_range, expected",
        [
            pytest.param(
                RoadTypeEnum.MOTORWAY, (0.2, 0.5), [3.0, 5.0], id="Motorway 0.2"
            ),
            pytest.param(
                RoadTypeEnum.MOTORWAY, (0.5, 1.2), [2.0, 4.0], id="Motorway 0.5"
            ),
        ],
    )
    def test_get_duration_steps(
        self,
        valid_resilience_curves: ResilienceCurves,
        link_type: RoadTypeEnum,
        hazard_range: tuple[float, float],
        expected: list[float],
    ):
        # 1. Execute test
        _result = valid_resilience_curves.get_duration_steps(link_type, hazard_range)

        # 2. Verify expectations
        assert _result == expected

    @pytest.mark.parametrize(
        "link_type, hazard_range, expected",
        [
            pytest.param(
                RoadTypeEnum.MOTORWAY, (0.2, 0.5), [1.0, 0.4], id="Motorway 0.2"
            ),
            pytest.param(
                RoadTypeEnum.MOTORWAY, (0.5, 1.2), [1.0, 0.3], id="Motorway 0.5"
            ),
        ],
    )
    def test_get_functionality_loss_ratio(
        self,
        valid_resilience_curves: ResilienceCurves,
        link_type: RoadTypeEnum,
        hazard_range: tuple[float, float],
        expected: list[float],
    ):
        # 1. Execute test
        _result = valid_resilience_curves.get_functionality_loss_ratio(
            link_type, hazard_range
        )

        # 2. Verify expectations
        assert _result == expected

    @pytest.mark.parametrize(
        "link_type, hazard_range, expected",
        [
            pytest.param(RoadTypeEnum.MOTORWAY, (0.2, 0.5), 5.0, id="Motorway 0.2"),
            pytest.param(RoadTypeEnum.MOTORWAY, (0.5, 1.2), 3.2, id="Motorway 0.5"),
        ],
    )
    def test_calculate_disruption(
        self,
        valid_resilience_curves: ResilienceCurves,
        link_type: RoadTypeEnum,
        hazard_range: tuple[float, float],
        expected: float,
    ):
        # 2. Execute test
        _result = valid_resilience_curves.calculate_disruption(link_type, hazard_range)

        # 3. Verify expectations
        assert _result == pytest.approx(expected)
