import pytest

from ra2ce.analysis.analysis_config_data.enums.part_of_day_enum import PartOfDayEnum
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.losses.traffic_intensities.traffic_intensities import (
    TrafficIntensities,
)


class TestTrafficIntensities:
    @pytest.mark.parametrize(
        "link_ids, expected",
        [
            pytest.param([2, 3, 5], [5, 7, 8], id="from list[int]"),
            pytest.param([(2, 3, 5)], [8], id="from tuple[int]"),
            pytest.param([2, (3, 5)], [5, 8], id="from combination"),
        ],
    )
    def test_get_traffic_intensity(
        self,
        traffic_intensities_data: dict[
            tuple[PartOfDayEnum, TripPurposeEnum], list[int]
        ],
        link_ids: list[int | tuple[int, int]],
        expected: list[int],
    ):
        # 1. Define test data
        _traffic_intensities = TrafficIntensities(link_id=list(range(1, 6)))
        for _key in traffic_intensities_data:
            _traffic_intensities.intensities[_key] = traffic_intensities_data[_key]

        _part_of_day = PartOfDayEnum.DAY
        _trip_purpose = TripPurposeEnum.BUSINESS

        # 2. Execute test
        _result = _traffic_intensities.get_intensities(
            link_ids,
            _part_of_day,
            _trip_purpose,
        )

        # 3. Verify expectations
        assert _result == expected
