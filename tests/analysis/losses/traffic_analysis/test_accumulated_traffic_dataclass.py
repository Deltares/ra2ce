import pytest

from ra2ce.analysis.losses.traffic_analysis.accumulated_traffic_dataclass import (
    AccumulatedTraffic,
)


@pytest.fixture
def valid_accumulated_traffic() -> AccumulatedTraffic:
    yield AccumulatedTraffic(1, 2, 3)


multiplicate_cases = [
    pytest.param(
        AccumulatedTraffic(2, 2, 2),
        AccumulatedTraffic(2, 4, 6),
        id="With an AccumulatedTraffic object.",
    ),
    pytest.param(3.0, AccumulatedTraffic(3, 6, 9), id="With a float."),
    pytest.param(4, AccumulatedTraffic(4, 8, 12), id="With an int."),
]
addition_cases = [
    pytest.param(
        AccumulatedTraffic(2, 2, 2),
        AccumulatedTraffic(3, 4, 5),
        id="With an AccumulatedTraffic object.",
    ),
    pytest.param(3.0, AccumulatedTraffic(4, 5, 6), id="With a float."),
    pytest.param(4, AccumulatedTraffic(5, 6, 7), id="With an int."),
]


class TestAccumulatedTrafficDataclass:
    def test_multiply_wrong_type_raises_error(self):
        with pytest.raises(TypeError) as exc_err:
            AccumulatedTraffic() * "Lorem ipsum"
        assert (
            str(exc_err.value)
            == "It is not possible to multiply AccumulatedTraffic with a value of type str."
        )

    def test_addition_wrong_type_raises_error(self):
        with pytest.raises(TypeError) as exc_err:
            AccumulatedTraffic() + "Lorem ipsum"
        assert (
            str(exc_err.value)
            == "It is not possible to sum AccumulatedTraffic with a value of type str."
        )

    @pytest.mark.parametrize("right_value, expected_result", multiplicate_cases)
    def test_multiply_values(
        self,
        valid_accumulated_traffic: AccumulatedTraffic,
        right_value: AccumulatedTraffic,
        expected_result: AccumulatedTraffic,
    ):
        # 2. Run test.
        _result = valid_accumulated_traffic * right_value

        # 3. Verify expectation.
        assert _result != valid_accumulated_traffic
        assert _result != right_value
        assert _result.utilitarian == expected_result.utilitarian
        assert _result.egalitarian == expected_result.egalitarian
        assert _result.prioritarian == expected_result.prioritarian

    @pytest.mark.parametrize("right_value, expected_result", multiplicate_cases)
    def test_multiply_values_compressed_operator(
        self,
        valid_accumulated_traffic: AccumulatedTraffic,
        right_value: AccumulatedTraffic,
        expected_result: AccumulatedTraffic,
    ):
        # 2. Run test.
        valid_accumulated_traffic *= right_value

        # 3. Verify expectation.
        assert valid_accumulated_traffic != right_value
        assert valid_accumulated_traffic.utilitarian == expected_result.utilitarian
        assert valid_accumulated_traffic.egalitarian == expected_result.egalitarian
        assert valid_accumulated_traffic.prioritarian == expected_result.prioritarian

    @pytest.mark.parametrize("right_value, expected_result", addition_cases)
    def test_add_values(
        self,
        valid_accumulated_traffic: AccumulatedTraffic,
        right_value: AccumulatedTraffic,
        expected_result: AccumulatedTraffic,
    ):
        # 2. Run test.
        _result = valid_accumulated_traffic + right_value

        # 3. Verify expectation.
        assert _result != valid_accumulated_traffic
        assert _result != right_value
        assert _result.utilitarian == expected_result.utilitarian
        assert _result.egalitarian == expected_result.egalitarian
        assert _result.prioritarian == expected_result.prioritarian

    @pytest.mark.parametrize("right_value, expected_result", addition_cases)
    def test_add_values_compressed(
        self,
        valid_accumulated_traffic: AccumulatedTraffic,
        right_value: AccumulatedTraffic,
        expected_result: AccumulatedTraffic,
    ):
        # 2. Run test.
        valid_accumulated_traffic += right_value

        # 3. Verify expectation.
        assert valid_accumulated_traffic != right_value
        assert valid_accumulated_traffic.utilitarian == expected_result.utilitarian
        assert valid_accumulated_traffic.egalitarian == expected_result.egalitarian
        assert valid_accumulated_traffic.prioritarian == expected_result.prioritarian
