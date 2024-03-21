import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_indirect_enum import (
    AnalysisIndirectEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.indirect.losses import Losses
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum
from tests import test_data


class TestLosses:
    def test_initialize_no_data(self):
        # 1. Define test data
        _analysis = AnalysisSectionIndirect(part_of_day=None)
        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = Path("sth")

        _analysis_input = AnalysisInputWrapper.from_input(_analysis, _config)

        # 2. Run test.
        _losses = Losses(_analysis_input)

        # 3. Verify final expectations.
        assert isinstance(_losses, Losses)
        assert isinstance(_losses.analysis, AnalysisSectionIndirect)

    def test_initialize_with_data(self):
        # 1. Define test data
        _losses_csv_data = test_data.joinpath("losses", "csv_data_for_losses")
        _analysis = AnalysisSectionIndirect(
            part_of_day=None,
            resilience_curve_file=_losses_csv_data.joinpath("resilience_curve.csv"),
            traffic_intensities_file=_losses_csv_data.joinpath(
                "traffic_intensities.csv"
            ),
            values_of_time_file=_losses_csv_data.joinpath("values_of_time.csv"),
            name="single_link_redundancy_losses_test",
        )

        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = test_data.joinpath(
            "losses", "csv_data_for_losses"
        )

        _analysis_input = AnalysisInputWrapper.from_input(_analysis, _config)

        # 2. Run test.
        _losses = Losses(_analysis_input)

        # 3. Verify final expectations.
        assert isinstance(_losses, Losses)

    @pytest.mark.parametrize(
        "part_of_day",
        [pytest.param(PartOfDayEnum.DAY), pytest.param(PartOfDayEnum.EVENING)],
    )
    def test_calc_vlh(self, part_of_day: PartOfDayEnum):
        # 1. Define test data
        _config = AnalysisConfigWrapper()
        _losses_csv_data = test_data.joinpath("losses", "csv_data_for_losses")
        _config.config_data.input_path = _losses_csv_data

        _analysis = AnalysisSectionIndirect(
            analysis=AnalysisIndirectEnum.SINGLE_LINK_LOSSES,
            part_of_day=part_of_day,
            resilience_curve_file=_losses_csv_data.joinpath("resilience_curve.csv"),
            traffic_intensities_file=_losses_csv_data.joinpath(
                "traffic_intensities.csv"
            ),
            values_of_time_file=_losses_csv_data.joinpath("values_of_time.csv"),
            name="single_link_redundancy_losses_test",
            performance="diff_length",
        )

        _analysis_input = AnalysisInputWrapper.from_input(_analysis, _config)

        _losses = Losses(_analysis_input)

        # 2. Run test.
        _result = _losses.calc_vlh()
        _expected_result = pd.read_csv(
            test_data / "losses" / "csv_data_for_losses" / "results_test_calc_vlh.csv"
        )

        # 3. Verify final expectations.
        assert isinstance(_result, pd.DataFrame)
        assert "vlh_business_0.2_0.5" in _result
        pd.testing.assert_frame_equal(_result, _expected_result)
