import pandas as pd
import pytest

from ra2ce.analysis.losses.traffic_analysis.accumulated_traffic_dataclass import (
    AccumulatedTraffic,
)
from ra2ce.analysis.losses.traffic_analysis.equity_analysis import EquityAnalysis
from tests import slow_test, test_data, test_results
from tests.analysis.losses.traffic_analysis import (
    TrafficAnalysisInput,
    valid_traffic_analysis_input,
)

_equity_test_data = test_data.joinpath("equity_data")


class TestEquityAnalysis:
    @pytest.fixture
    def valid_equity_analysis(
        self,
        valid_traffic_analysis_input: TrafficAnalysisInput,
    ) -> EquityAnalysis:
        yield EquityAnalysis(
            valid_traffic_analysis_input.road_network,
            valid_traffic_analysis_input.od_table_data,
            valid_traffic_analysis_input.equity_data,
        )

    @slow_test
    def test_equity_analysis_with_valid_data(
        self,
        valid_equity_analysis: EquityAnalysis,
        request: pytest.FixtureRequest,
    ):
        # 1. Define test data.
        _test_result = test_results.joinpath(request.node.name + ".csv")
        if _test_result.exists():
            _test_result.unlink()

        # Define expected results.
        _expected_result = pd.read_csv(
            _equity_test_data.joinpath("expected_result.csv"),
            index_col=0,
            dtype={
                "u": str,
                "v": str,
                "traffic": float,
                "traffic_egalitarian": float,
                "traffic_prioritarian": float,
            },
        )
        assert isinstance(_expected_result, pd.DataFrame)
        assert len(_expected_result.values) == 358

        # 2. Run test.
        _result = valid_equity_analysis.optimal_route_od_link()

        # 3. Verify expectations.
        assert isinstance(_result, pd.DataFrame)
        _result.to_csv(_test_result)

        assert not any(_result[["u", "v"]].duplicated())

        def _sort_dataframe(traffic_df: pd.DataFrame) -> pd.DataFrame:
            return traffic_df.sort_values(by=["u", "v"]).reset_index(drop=True)

        pd.testing.assert_frame_equal(
            _sort_dataframe(_expected_result), _sort_dataframe(_result)
        )

    def test_equity_analysis_get_accumulated_traffic_from_node(
        self, valid_equity_analysis: EquityAnalysis
    ):
        # 1. Define test data.
        # Get some valid data, we will only check the type of output for this method.
        _total_d_nodes = 42
        _o_node = "A_22"

        # 2. Run test.
        _accumulated_traffic = valid_equity_analysis._get_accumulated_traffic_from_node(
            _o_node, _total_d_nodes
        )

        # 3. Verify expectations.
        assert isinstance(_accumulated_traffic, AccumulatedTraffic)
        assert _accumulated_traffic.egalitarian == 1
        assert _accumulated_traffic.utilitarian == pytest.approx(3.1097, 0.0001)
        assert _accumulated_traffic.prioritarian == pytest.approx(2.4615, 0.0001)
