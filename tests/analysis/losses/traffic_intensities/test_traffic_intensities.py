import pytest

from ra2ce.analysis.analysis_config_data.enums.part_of_day_enum import PartOfDayEnum
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.losses.traffic_intensities.traffic_intensities import (
    TrafficIntensities,
)


class TestTrafficIntensities:
    @pytest.mark.parametrize(
        "link_id, expected",
        [
            pytest.param(2, 5.0, id="from int (link 2)"),
            pytest.param(5, 8.0, id="from int (link 5)"),
            pytest.param((2, 5), 8.0, id="from tuple[int]"),
        ],
    )
    def test_calculate_traffic_intensity(
        self,
        traffic_intensities_data: dict[
            tuple[PartOfDayEnum, TripPurposeEnum], list[int]
        ],
        link_id: int | tuple[int, int],
        expected: float,
    ):
        # 1. Define test data
        _traffic_intensities = TrafficIntensities(link_id=list(range(1, 6)))
        for _key in traffic_intensities_data:
            _traffic_intensities.intensities[_key] = traffic_intensities_data[_key]

        _part_of_day = PartOfDayEnum.DAY
        _trip_purpose = TripPurposeEnum.BUSINESS

        # 2. Execute test
        _result = _traffic_intensities.calculate_intensity(
            link_id,
            _part_of_day,
            _trip_purpose,
        )

        # 3. Verify expectations
        assert _result == pytest.approx(expected)
