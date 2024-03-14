import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_config_data.enums.analysis_indirect_enum import AnalysisIndirectEnum
from ra2ce.analysis.indirect.losses import Losses
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum
from tests import test_data


class TestLosses:

    def test_initialize_no_data(self):
        # 1. Define test data
        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = Path("sth")
        _analysis = AnalysisSectionIndirect(
            part_of_day=None)

        # 2. Run test.
        _losses = Losses(
            _config.graph_files.base_graph_hazard,
            _analysis,
            _config.config_data.input_path,
            _config.config_data.static_path,
            _config.config_data.output_path,
            [],
        )

        # 3. Verify final expectations.
        assert isinstance(_losses, Losses)
        assert isinstance(_losses.analysis, AnalysisSectionIndirect)

    def test_initialize_with_data(self):
        # 1. Define test data
        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = Path("sth")
        _analyses = AnalysisSectionIndirect(
            part_of_day=None,
            resilience_curve_file=test_data / "losses" / "csv_data_for_losses" / "resilience_curve.csv",
            traffic_intensities_file=test_data / "losses" / "csv_data_for_losses" / "traffic_intensities.csv",
            values_of_time_file=test_data / "losses" / "csv_data_for_losses" / "values_of_time.csv",
            name="single_link_redundancy_losses_test"
        )
        _config.input_path = test_data / "losses" / "csv_data_for_losses"

        # 2. Run test.

        _losses = Losses(
            _config.graph_files.base_graph_hazard,
            _analyses,
            _config.config_data.input_path,
            _config.config_data.static_path,
            _config.config_data.output_path,
            [],
        )

        # 3. Verify final expectations.
        assert isinstance(_losses, Losses)

    @pytest.mark.parametrize(
        "part_of_day",
        [pytest.param(PartOfDayEnum.DAY), pytest.param(PartOfDayEnum.EVENING)],
    )
    def test_calc_vlh(self, part_of_day: str):
        # 1. Define test data
        _config = AnalysisConfigWrapper()
        _config.config_data.input_path = test_data / "losses" / "csv_data_for_losses"
        _analyses = AnalysisSectionIndirect(
            analysis=AnalysisIndirectEnum.SINGLE_LINK_LOSSES,
            part_of_day=part_of_day,
            resilience_curve_file=test_data / "losses" / "csv_data_for_losses" / "resilience_curve.csv",
            traffic_intensities_file=test_data / "losses" / "csv_data_for_losses" / "traffic_intensities.csv",
            values_of_time_file=test_data / "losses" / "csv_data_for_losses" / "values_of_time.csv",
            name="single_link_redundancy_losses_test",
            performance="diff_length"

        )

        _losses = Losses(
            _config.graph_files.base_graph_hazard,
            _analyses,
            _config.config_data.input_path,
            _config.config_data.static_path,
            _config.config_data.output_path,
            [],
        )

        # 2. Run test.
        _result = _losses.calc_vlh(
        )
        _expected_result = pd.read_csv(
            test_data / "losses" / "csv_data_for_losses" / "results_test_calc_vlh.csv"
        )

        # 3. Verify final expectations.
        assert isinstance(_result, pd.DataFrame)
        assert "vlh_business_0.2_0.5" in _result
        pd.testing.assert_frame_equal(_result, _expected_result)
