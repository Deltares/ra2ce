from typing import Iterator

import pytest

from ra2ce.network.avg_speed.avg_speed import AvgSpeed
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class TestAvgSpeed:
    @pytest.mark.parametrize(
        "road_type, expected",
        [
            pytest.param(None, [RoadTypeEnum.INVALID], id="None"),
            pytest.param("tertiary", [RoadTypeEnum.TERTIARY], id="from str"),
            pytest.param(
                "['secondary', 'tertiary']",
                [RoadTypeEnum.SECONDARY, RoadTypeEnum.TERTIARY],
                id="from str(list)",
            ),
            pytest.param(
                ["secondary", "tertiary"],
                [RoadTypeEnum.SECONDARY, RoadTypeEnum.TERTIARY],
                id="from list[str]",
            ),
            pytest.param(dict(), [RoadTypeEnum.INVALID], id="Other type"),
        ],
    )
    def test_get_road_type_list(
        self,
        road_type: None | str | list[str],
        expected: list[RoadTypeEnum],
    ):
        # 1. Define test data

        # 2. Execute test
        _road_type_list = AvgSpeed.get_road_type_list(road_type)

        # 3. Verify expectations
        assert isinstance(_road_type_list, list)
        assert _road_type_list == expected

    @pytest.fixture(
        params=[
            pytest.param([RoadTypeEnum.TERTIARY], id="from Enum"),
            pytest.param(
                [RoadTypeEnum.SECONDARY, RoadTypeEnum.TERTIARY], id="from sorted list[Enum]"
            ),
            pytest.param(
                [RoadTypeEnum.TERTIARY, RoadTypeEnum.SECONDARY], id="from unsorted list[Enum]"
            ),
        ],
        name="road_type",
    )
    def _get_road_type(
        self, request: pytest.FixtureRequest
    ) -> Iterator[list[RoadTypeEnum]]:
        yield request.param

    def test_set_avg_speed(self, road_type: list[RoadTypeEnum]):
        # 1. Define test data
        _avg_speed = AvgSpeed()
        _speed = 60.0

        # 2. Execute test
        _avg_speed.set_avg_speed(road_type, _speed)

        # 3. Verify expectations
        assert len(_avg_speed.speed_per_road_type) == 1
        _speeds = list(_avg_speed.speed_per_road_type.values())
        assert _speeds[0] == _speed

    def test_get_avg_speed(self, road_type: list[RoadTypeEnum]):
        # 1. Define test data
        _avg_speed = AvgSpeed()
        _expected_speed = 60.0
        _avg_speed.set_avg_speed(road_type, _expected_speed)

        # 2. Execute test
        _speed = _avg_speed.get_avg_speed(road_type)

        # 3. Verify expectations
        assert _speed == _expected_speed

    def test_get_avg_speed_default(self):
        # 1. Define test data
        _avg_speed = AvgSpeed()
        _road_type = [RoadTypeEnum.TERTIARY]

        # 2. Execute test
        _speed = _avg_speed.get_avg_speed(_road_type)

        # 3. Verify expectations
        assert _speed == 50.0

    @pytest.mark.parametrize(
        "road_type, expected",
        [
            pytest.param(
                [RoadTypeEnum.TERTIARY],
                RoadTypeEnum.TERTIARY.config_value,
                id="from Enum",
            ),
            pytest.param(
                [RoadTypeEnum.SECONDARY, RoadTypeEnum.TERTIARY],
                f"['{RoadTypeEnum.SECONDARY.config_value}', '{RoadTypeEnum.TERTIARY.config_value}']",
                id="from list[Enum]",
            ),
        ],
    )
    def test_get_key_str(self, road_type: list[RoadTypeEnum], expected: str):
        # 1. Define test data
        _avg_speed = AvgSpeed()
        _avg_speed.set_avg_speed(road_type, 60.0)
        _road_types = list(_avg_speed.speed_per_road_type.keys())

        # 2. Execute test
        _key_str = str(_road_types[0])

        # 3. Verify expectations
        assert _key_str == expected
