from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.losses.traffic_intensities.traffic_intensities import (
    TrafficIntensities,
)
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum


class TestTrafficIntensities:
    def test_get_traffic_intensity(
        self,
        traffic_intensities_data: list[
            tuple[int, int, int, int, int, int, int, int, int, int, int]
        ],
        traffic_intensities_names: list[str],
    ):
        # 1. Define test data
        _traffic_intensities = TrafficIntensities()
        _data = list(zip(*traffic_intensities_data))
        for i, _field_name in enumerate(traffic_intensities_names):
            setattr(
                _traffic_intensities,
                _field_name,
                _data[i],
            )

        _part_of_day = PartOfDayEnum.DAY
        _trip_purpose = TripPurposeEnum.BUSINESS
        _link_ids = [2, 3, 5]

        # 2. Execute test
        _result = _traffic_intensities.get_intensity(
            _link_ids,
            _part_of_day,
            _trip_purpose,
        )

        # 3. Verify expectations
        assert _result == 20
