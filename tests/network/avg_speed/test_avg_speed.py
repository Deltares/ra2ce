from typing import Iterator

import pytest

from ra2ce.network.avg_speed.avg_speed import AvgSpeed
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class TestAvgSpeed:
    @pytest.fixture(
        params=[
            pytest.param("tertiary", id="from str"),
            pytest.param("['tertiary', 'secondary']", id="from str(list)"),
            pytest.param(RoadTypeEnum.TERTIARY, id="from Enum"),
            pytest.param(
                [RoadTypeEnum.TERTIARY, RoadTypeEnum.SECONDARY], id="from list[Enum]"
            ),
        ],
        name="road_type",
    )
    def _get_road_type(
        self, request: pytest.FixtureRequest
    ) -> Iterator[str | RoadTypeEnum | list[RoadTypeEnum]]:
        yield request.param

    def test_set_avg_speed(self, road_type: str | RoadTypeEnum | list[RoadTypeEnum]):
        # 1. Define test data
        _avg_speed = AvgSpeed()
        _speed = 60.0

        # 2. Execute test
        _avg_speed.set_avg_speed(road_type, _speed)

        # 3. Verify expectations
        assert len(_avg_speed.speed_per_road_type) == 1
        _speeds = list(_avg_speed.speed_per_road_type.values())
        assert _speeds[0] == _speed

    def test_get_avg_speed(self, road_type: str | RoadTypeEnum | list[RoadTypeEnum]):
        # 1. Define test data
        _avg_speed = AvgSpeed()
        _expected_speed = 60.0
        _avg_speed.set_avg_speed(road_type, _expected_speed)

        # 2. Execute test
        _speed = _avg_speed.get_avg_speed(road_type)

        # 3. Verify expectations
        assert _speed == _expected_speed

    @pytest.mark.parametrize(
        "road_type, expected",
        [
            pytest.param(
                RoadTypeEnum.TERTIARY,
                RoadTypeEnum.TERTIARY.config_value,
                id="from Enum",
            ),
            pytest.param(
                [RoadTypeEnum.TERTIARY, RoadTypeEnum.SECONDARY],
                f"['{RoadTypeEnum.TERTIARY.config_value}', '{RoadTypeEnum.SECONDARY.config_value}']",
                id="from list[Enum]",
            ),
        ],
    )
    def test_get_key_str(
        self, road_type: str | RoadTypeEnum | list[RoadTypeEnum], expected: str
    ):
        # 1. Define test data
        _avg_speed = AvgSpeed()
        _avg_speed.set_avg_speed(road_type, 60.0)
        _road_types = list(_avg_speed.speed_per_road_type.keys())

        # 2. Execute test
        _key_str = str(_road_types[0])

        # 3. Verify expectations
        assert _key_str == expected
