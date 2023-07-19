import pytest
import pandas as pd
from pathlib import Path
from ra2ce.analyses.indirect.traffic_analysis.traffic_analysis_factory import (
    TrafficAnalysisFactory,
)


class TestTrafficAnalysisFactory:
    @pytest.mark.parametrize(
        "file_arg",
        [
            pytest.param("", id="Empty string"),
            pytest.param(None, id="No value given"),
            pytest.param(
                Path("does_not_exist.geojson"), id="Non-existing geojson file"
            ),
        ],
    )
    def test_read_equity_weights_without_file(self, file_arg: Path):
        # 1. Run test.
        _result = TrafficAnalysisFactory.read_equity_weights(file_arg)

        # 2. Verify expectations.
        assert isinstance(_result, pd.DataFrame)
        assert _result.empty
