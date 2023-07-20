from ra2ce.analyses.indirect.traffic_analysis.equity_analysis import (
    EquityAnalysis,
)
from tests import slow_test, test_results, test_data
import pytest
import pandas as pd

from tests.analyses.indirect.traffic_analysis import (
    TrafficAnalysisInput,
    valid_traffic_analysis_input,
)

_equity_test_data = test_data.joinpath("equity_data")


class TestEquityAnalysis:
    @slow_test
    def test_equity_analysis_with_valid_data(
        self,
        valid_traffic_analysis_input: TrafficAnalysisInput,
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
        assert len(_expected_result.values) == 359

        # 2. Run test.
        _result = EquityAnalysis(
            valid_traffic_analysis_input.gdf_data,
            valid_traffic_analysis_input.od_table_data,
            valid_traffic_analysis_input.destination_names,
            valid_traffic_analysis_input.equity_data,
        ).optimal_route_od_link()

        # 3. Verify expectations.
        assert isinstance(_result, pd.DataFrame)
        _result.to_csv(_test_result)

        assert not any(_result[["u", "v"]].duplicated())
        pd.testing.assert_frame_equal(_expected_result, _result)

    def test_equity_analysis_get_accumulated_traffic_from_node(self):
        pass
