import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import geopandas as gpd

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionIndirect, AnalysisConfigData,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purposes import TripPurposeEnum
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_indirect_enum import (
    AnalysisIndirectEnum,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.indirect.losses import Losses
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_data


class TestLosses:
    def test_initialize_no_data(self):
        # 1. Define test data

        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()
        _valid_analysis_ini = test_data / "losses" / "analyses.ini"
        _config = AnalysisConfigWrapper.from_data_with_network(
            _valid_analysis_ini, _config_data, _network_config
        )

        _config.config_data.input_path = Path("sth")
        _analysis = AnalysisSectionIndirect(
            part_of_day=None)

        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=_analysis,
            analysis_config=_config,
            graph_file=_config.graph_files.base_graph_hazard,
            graph_file_hazard=_config.graph_files.base_graph_hazard,
        )

        with pytest.raises(PermissionError):
            _losses = Losses(_analysis_input, _config)

    def test_initialize_with_data(self):
        # 1. Define test data
        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()
        _valid_analysis_ini = test_data / "losses" / "analyses.ini"
        _config = AnalysisConfigWrapper.from_data_with_network(
            _valid_analysis_ini, _config_data, _network_config
        )

        # Add extra arguments to config_data
        _config.config_data.input_path = test_data / "losses" / "csv_data_for_losses"
        _config_data.network.file_id = "link_id"
        _config_data.network.link_type_column = "link_type"

        _analysis = AnalysisSectionIndirect(
            part_of_day=PartOfDayEnum.DAY,
            resilience_curve_file=test_data / "losses" / "csv_data_for_losses" / "resilience_curve.csv",
            traffic_intensities_file=test_data / "losses" / "csv_data_for_losses" / "traffic_intensities.csv",
            values_of_time_file=test_data / "losses" / "csv_data_for_losses" / "values_of_time.csv",
            name="single_link_redundancy_losses_test",
            trip_purposes=[TripPurposeEnum.BUSINESS, TripPurposeEnum.COMMUTE]

        )

        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=_analysis,
            analysis_config=_config,
            graph_file=_config.graph_files.base_graph_hazard,
            graph_file_hazard=_config.graph_files.base_graph_hazard,
        )

        # 2. Run test.
        _losses = Losses(_analysis_input, _config)

        # 3. Verify final expectations.
        assert isinstance(_losses, Losses)

    @pytest.mark.parametrize(
        "part_of_day",
        [
            pytest.param(PartOfDayEnum.DAY),
            # pytest.param(PartOfDayEnum.EVENING)
        ],
    )
    def test_calc_vlh(self, part_of_day: PartOfDayEnum):
        # 1. Define test data
        _losses_csv_data = test_data.joinpath("losses", "csv_data_for_losses")

        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()
        _valid_analysis_ini = test_data / "losses" / "analyses.ini"
        _config = AnalysisConfigWrapper.from_data_with_network(
            _valid_analysis_ini, _config_data, _network_config
        )

        _config_data.network.file_id = "link_id"
        _config_data.network.link_type_column = "link_type"
        _config.config_data.input_path = test_data / "losses" / "csv_data_for_losses"

        _analysis = AnalysisSectionIndirect(
            part_of_day=part_of_day,
            resilience_curve_file=_losses_csv_data.joinpath("resilience_curve.csv"),
            traffic_intensities_file=_losses_csv_data.joinpath(
                "traffic_intensities.csv"
            ),
            values_of_time_file=_losses_csv_data.joinpath("values_of_time.csv"),
            name="single_link_redundancy_losses_test",
            trip_purposes=[TripPurposeEnum.BUSINESS, TripPurposeEnum.COMMUTE],
            weighing=WeighingEnum.LENGTH,
            hours_per_day=10,

        )

        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=_analysis,
            analysis_config=_config,
            graph_file=_config.graph_files.base_graph_hazard,
            graph_file_hazard=_config.graph_files.base_graph_hazard,
        )

        _losses = Losses(_analysis_input, _config)
        _losses._get_disrupted_criticality_analysis_results(gpd.read_file(test_data / 'losses' / 'csv_data_for_losses' / 'single_link_redundancy_losses_test.csv'))


        # 2. Run test.

        _result = _losses.calculate_vehicle_loss_hours()

        _expected_result = pd.read_csv(
            test_data / "losses" / "csv_data_for_losses" / "results_test_calc_vlh.csv"
        )

        # 3. Verify final expectations.
        assert isinstance(_result, pd.DataFrame)
        assert "vlh_business_EV1_ma" in _result
        pd.testing.assert_frame_equal(_result[['vlh_business_EV1_ma', 'vlh_commute_EV1_ma']],
                                      _expected_result[['vlh_business_EV1_ma', 'vlh_commute_EV1_ma']])
