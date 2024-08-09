import pytest

from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum


class TestGetWlPrefix:
    @pytest.mark.parametrize(
        "aggregate_wl, expected_prefix",
        [
            pytest.param(
                AggregateWlEnum.MAX,
                "ma",
                id=AggregateWlEnum.MAX.name.lower(),
            ),
            pytest.param(
                AggregateWlEnum.MIN,
                "mi",
                id=AggregateWlEnum.MIN.name.lower(),
            ),
            pytest.param(
                AggregateWlEnum.MEAN,
                "me",
                id=AggregateWlEnum.MEAN.name.lower(),
            ),
        ],
    )
    def test_aggregate_wl_prefix(
        self, aggregate_wl: AggregateWlEnum, expected_prefix: str
    ):
        # 1./2. Define test data / Run test
        _prefix = aggregate_wl.get_wl_prefix()

        # 3. Verify results
        assert _prefix == expected_prefix
