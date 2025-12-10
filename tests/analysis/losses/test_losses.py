from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import LineString

from ra2ce.analysis.analysis_base import AnalysisBase
from ra2ce.analysis.analysis_config_data import LossesConfigDataTypes
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_data.base_link_losses_config_data import (
    BaseLinkLossesConfigData,
    SingleLinkLossesConfigData,
)
from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_config_data.losses_analysis_config_data_protocol import (
    BaseLossesAnalysisConfigData,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.losses_base import LossesBase
from ra2ce.analysis.losses.multi_link_losses import MultiLinkLosses
from ra2ce.analysis.losses.single_link_losses import SingleLinkLosses
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_data


class TestLosses:
    @pytest.fixture(
        params=[
            pytest.param(SingleLinkLosses, id="Single link losses analysis"),
            pytest.param(MultiLinkLosses, id="Multi link losses analysis"),
        ],
        name="losses_analysis",
    )
    def _get_losses_analysis(
        self, request: pytest.FixtureRequest
    ) -> Iterator[AnalysisLossesProtocol]:
        _analysis_losses_type = request.param
        assert issubclass(_analysis_losses_type, LossesBase)
        assert issubclass(_analysis_losses_type, AnalysisLossesProtocol)
        yield _analysis_losses_type

    def test_initialize_no_data(self, losses_analysis: type[AnalysisLossesProtocol]):
        # 1. Define test data

        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()
        _valid_analysis_ini = test_data.joinpath("losses", "analyses.ini")
        _config = AnalysisConfigWrapper.from_data_with_network(
            _valid_analysis_ini, _config_data, _network_config
        )

        _config.config_data.input_path = Path("sth")
        _analysis = BaseLossesAnalysisConfigData(traffic_period=None)

        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=_analysis,
            analysis_config=_config,
            graph_file=_config.graph_files.base_graph_hazard,
            graph_file_hazard=_config.graph_files.base_graph_hazard,
        )

        # 2. Run test.
        _losses = losses_analysis(_analysis_input, _config)

        # 3. Verify final expectations.
        assert isinstance(_losses, LossesBase)
        assert isinstance(_losses, losses_analysis)
        assert isinstance(_losses, AnalysisBase)

    def test_initialize_with_data(
        self,
        losses_analysis: type[AnalysisLossesProtocol],
        resilience_curves_csv: Path,
        traffic_intensities_csv: Path,
        time_values_csv: Path,
    ):
        @dataclass
        class MockedLossesAnalysisConfigData(BaseLossesAnalysisConfigData):
            config_name: str = "mocked_losses_analysis_config_data"
        # 1. Define test data
        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()
        _valid_analysis_ini = test_data.joinpath("losses", "analyses.ini")
        _config = AnalysisConfigWrapper.from_data_with_network(
            _valid_analysis_ini, _config_data, _network_config
        )

        # Add extra arguments to config_data
        _config.config_data.input_path = test_data.joinpath(
            "losses", "csv_data_for_losses"
        )
        _config_data.network.file_id = "link_id"
        _config_data.network.link_type_column = "link_type"

        _analysis = SingleLinkLossesConfigData(
            traffic_period=TrafficPeriodEnum.DAY,
            resilience_curves_file=resilience_curves_csv,
            traffic_intensities_file=traffic_intensities_csv,
            values_of_time_file=time_values_csv,
            name="single_link_redundancy_losses_test",
            trip_purposes=[TripPurposeEnum.BUSINESS, TripPurposeEnum.COMMUTE],
        )

        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=_analysis,
            analysis_config=_config,
            graph_file=_config.graph_files.base_graph_hazard,
            graph_file_hazard=_config.graph_files.base_graph_hazard,
        )

        # 2. Run test.
        _losses = losses_analysis(_analysis_input, _config)

        # 3. Verify final expectations.
        assert isinstance(_losses, LossesBase)
        assert isinstance(_losses, losses_analysis)
        assert isinstance(_losses, AnalysisBase)

    @pytest.mark.parametrize("losses_config_type", [pytest.param(_lct, id=_lct.__name__) for _lct in LossesConfigDataTypes])
    def test_calc_vlh(
        self,
        losses_config_type: type[BaseLinkLossesConfigData],
        resilience_curves_csv: Path,
        traffic_intensities_csv: Path,
        time_values_csv: Path,
    ):
        def create_linestring(row):
            node_a_coords = (
                node_coordinates_df.loc[
                    node_coordinates_df["node_id"] == row["node_A"], "longitude"
                ].values[0],
                node_coordinates_df.loc[
                    node_coordinates_df["node_id"] == row["node_A"], "latitude"
                ].values[0],
            )
            node_b_coords = (
                node_coordinates_df.loc[
                    node_coordinates_df["node_id"] == row["node_B"], "longitude"
                ].values[0],
                node_coordinates_df.loc[
                    node_coordinates_df["node_id"] == row["node_B"], "latitude"
                ].values[0],
            )
            return LineString([node_a_coords, node_b_coords])

        # 1. Define test data
        # Define latitude and longitude values for each node
        node_coordinates_data = {
            "node_id": [0, 1, 2, 3],
            "latitude": [40.7128, 34.0522, 51.5074, 48.8566],
            "longitude": [-74.0060, -118.2437, -0.1278, 2.3522],
        }
        node_coordinates_df = pd.DataFrame(node_coordinates_data)

        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()
        _network_config.config_data.hazard.aggregate_wl = AggregateWlEnum.MAX
        _valid_analysis_ini = test_data.joinpath("losses", "analyses.ini")
        _config = AnalysisConfigWrapper.from_data_with_network(
            _valid_analysis_ini, _config_data, _network_config
        )

        _config_data.network.file_id = "link_id"
        _config_data.network.link_type_column = "link_type"
        _config.config_data.input_path = test_data.joinpath(
            "losses" "csv_data_for_losses"
        )

        _analysis = losses_config_type(
            traffic_period=TrafficPeriodEnum.DAY,
            hours_per_traffic_period=24,
            # threshold=0,
            production_loss_per_capita_per_hour=20,
            resilience_curves_file=resilience_curves_csv,
            traffic_intensities_file=traffic_intensities_csv,
            values_of_time_file=time_values_csv,
            name="single_link_redundancy_losses_test",
            trip_purposes=[TripPurposeEnum.BUSINESS, TripPurposeEnum.COMMUTE],
            weighing=WeighingEnum.LENGTH,
        )

        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=_analysis,
            analysis_config=_config,
            graph_file=_config.graph_files.base_graph_hazard,
            graph_file_hazard=_config.graph_files.base_graph_hazard,
        )

        _losses = SingleLinkLosses(_analysis_input, _config)

        _losses.criticality_analysis = pd.read_csv(
            test_data.joinpath(
                "losses",
                "csv_data_for_losses",
                "single_link_redundancy_losses_test.csv",
            ),
            sep=",",
            on_bad_lines="skip",
        )
        _losses.criticality_analysis[["EV1_ma", "diff_length", "detour"]].astype(float)

        # Create a GeoDataFrame
        _losses.criticality_analysis["alt_nodes"] = _losses.criticality_analysis[
            "alt_nodes"
        ].apply(eval)
        _losses.criticality_analysis["geometry"] = _losses.criticality_analysis.apply(
            create_linestring, axis=1
        )
        _losses.criticality_analysis = gpd.GeoDataFrame(_losses.criticality_analysis)

        _losses._get_disrupted_criticality_analysis_results(
            _losses.criticality_analysis
        )

        # 2. Run test.

        _result = _losses.calculate_vehicle_loss_hours()

        _expected_result = pd.read_csv(
            test_data.joinpath(
                "losses", "csv_data_for_losses", "results_test_calc_vlh.csv"
            )
        )
        _expected_result.reset_index(inplace=True)

        # 3. Verify final expectations.
        assert isinstance(_result, pd.DataFrame)
        assert "vlh_business_EV1_ma" in _result
        pd.testing.assert_frame_equal(
            _result[["vlh_business_EV1_ma", "vlh_commute_EV1_ma"]],
            _expected_result[["vlh_business_EV1_ma", "vlh_commute_EV1_ma"]],
        )
        assert "vlh_business_EV2_mi" in _result
        pd.testing.assert_frame_equal(
            _result[["vlh_business_EV2_mi", "vlh_EV2_mi_total"]],
            _expected_result[["vlh_business_EV2_mi", "vlh_EV2_mi_total"]],
        )
        assert "vlh_business_RP100_me" in _result
        pd.testing.assert_frame_equal(
            _result[["vlh_business_RP100_me", "vlh_RP100_me_total"]],
            _expected_result[["vlh_business_RP100_me", "vlh_RP100_me_total"]],
        )
