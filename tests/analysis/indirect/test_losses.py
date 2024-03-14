import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_indirect_enum import AnalysisIndirectEnum
from ra2ce.analysis.indirect.losses import Losses
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum
from tests import test_data


class TestLosses:

    def test_initialize_no_data(self):
        # 1. Define test data
        _config = AnalysisConfigData(input_path=Path("sth"))
        _analyses = AnalysisSectionIndirect(
            part_of_day=None,
        )

        # 2. Run test.

        _losses = Losses(_config, _analyses)

        # 3. Verify final expectations.
        assert isinstance(_losses, Losses)

    def test_initialize_with_data(self):
        # 1. Define test data
        _config = AnalysisConfigData(input_path=test_data / "losses")
        _analyses = AnalysisSectionIndirect(
            part_of_day=None,
            resilience_curve_file=test_data / "losses" / "csv_data_for_losses" / "resilience_curve.csv",
            traffic_intensities_file=test_data / "losses" / "csv_data_for_losses" / "traffic_intensities.csv",
            values_of_time_file=test_data / "losses" / "csv_data_for_losses" / "values_of_time.csv",
            name="single_link_redundancy_losses_test"
        )
        _config.input_path = test_data / "losses" / "csv_data_for_losses"


        # 2. Run test.

        _losses = Losses(_config, _analyses)

        # 3. Verify final expectations.
        assert isinstance(_losses, Losses)

    @pytest.mark.parametrize(
        "part_of_day",
        # [pytest.param(PartOfDayEnum.DAY), pytest.param(PartOfDayEnum.EVENING)],
        [pytest.param(PartOfDayEnum.DAY)],
    )
    def test_calc_vlh(self, part_of_day: str):
        # 1. Define test data
        # TODO: Not sure of the input format values float of series?
        _config = AnalysisConfigData(input_path=Path("sth"))
        _analyses = AnalysisSectionIndirect(
            analysis=AnalysisIndirectEnum.SINGLE_LINK_LOSSES,
            part_of_day=part_of_day,
            resilience_curve_file=test_data / "losses" / "csv_data_for_losses" / "resilience_curve.csv",
            traffic_intensities_file=test_data / "losses" / "csv_data_for_losses" / "traffic_intensities.csv",
            values_of_time_file=test_data / "losses" / "csv_data_for_losses" / "values_of_time.csv",
            name="single_link_redundancy_losses_test",
            performance="diff_length"

        )
        _config.input_path = test_data / "losses" / "csv_data_for_losses"

        _losses = Losses(_config, _analyses)


        # 2. Run test.
        _result = _losses.calc_vlh(
        )
        print(_result)

        # 3. Verify final expectations.
        assert isinstance(_result, pd.DataFrame)
        assert "vlh_business_0.2_0.5" in _result

