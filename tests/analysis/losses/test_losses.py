from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import LineString

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purposes import TripPurposeEnum
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.losses_base import LossesBase
from ra2ce.analysis.losses.multi_link_losses import MultiLinkLosses
from ra2ce.analysis.losses.single_link_losses import SingleLinkLosses
from ra2ce.network.network_config_data.enums.part_of_day_enum import PartOfDayEnum
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_data


class TestLosses:
    @pytest.mark.parametrize(
        "analysis", [pytest.param(SingleLinkLosses), pytest.param(MultiLinkLosses)]
    )
    def test_initialize_no_data(self, analysis: type[AnalysisLossesProtocol]):
        # 1. Define test data

        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()
        _valid_analysis_ini = test_data.joinpath("losses", "analyses.ini")
        _config = AnalysisConfigWrapper.from_data_with_network(
            _valid_analysis_ini, _config_data, _network_config
        )

        _config.config_data.input_path = Path("sth")
        _analysis = AnalysisSectionLosses(part_of_day=None)

        _analysis_input = AnalysisInputWrapper.from_input(
            analysis=_analysis,
            analysis_config=_config,
            graph_file=_config.graph_files.base_graph_hazard,
            graph_file_hazard=_config.graph_files.base_graph_hazard,
        )

        # 2. Run test.
        with pytest.raises(ValueError) as exc:
            _losses = analysis(_analysis_input, _config)

        # 3. Verify final expectations.
        assert (
            str(exc.value)
            == "traffic_intensities_file, resilience_curve_file, and values_of_time_file should be given"
        )

    @pytest.mark.parametrize(
        "analysis", [pytest.param(SingleLinkLosses), pytest.param(MultiLinkLosses)]
    )
    def test_initialize_with_data(self, analysis: type[AnalysisLossesProtocol]):
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

        _analysis = AnalysisSectionLosses(
            part_of_day=PartOfDayEnum.DAY,
            resilience_curve_file=test_data.joinpath(
                "losses", "csv_data_for_losses", "resilience_curve.csv"
            ),
            traffic_intensities_file=test_data.joinpath(
                "losses", "csv_data_for_losses", "traffic_intensities.csv"
            ),
            values_of_time_file=test_data.joinpath(
                "losses", "csv_data_for_losses", "values_of_time.csv"
            ),
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
        _losses = analysis(_analysis_input, _config)

        # 3. Verify final expectations.
        assert isinstance(_losses, LossesBase)
        assert isinstance(_losses, analysis)

    @pytest.mark.parametrize(
        "part_of_day",
        [
            pytest.param(PartOfDayEnum.DAY),
            # pytest.param(PartOfDayEnum.EVENING)
        ],
    )
    def test_calc_vlh(self, part_of_day: PartOfDayEnum):
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

        _losses_csv_data = test_data.joinpath("losses", "csv_data_for_losses")

        _config_data = AnalysisConfigData()
        _network_config = NetworkConfigWrapper()
        _valid_analysis_ini = test_data.joinpath("losses", "analyses.ini")
        _config = AnalysisConfigWrapper.from_data_with_network(
            _valid_analysis_ini, _config_data, _network_config
        )

        _config_data.network.file_id = "link_id"
        _config_data.network.link_type_column = "link_type"
        _config.config_data.input_path = test_data.joinpath(
            "losses" "csv_data_for_losses"
        )

        _analysis = AnalysisSectionLosses(
            part_of_day=part_of_day,
            threshold=0,
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
        _losses.intensities_simplified_graph = (
            _losses._get_intensities_simplified_graph()
        )
        _losses.vot_intensity_per_trip_collection = (
            _losses._get_vot_intensity_per_trip_purpose()
        )

        # 2. Run test.

        _result = _losses.calculate_vehicle_loss_hours()

        _expected_result = pd.read_csv(
            test_data.joinpath(
                "losses", "csv_data_for_losses", "results_test_calc_vlh.csv"
            )
        )

        # 3. Verify final expectations.
        assert isinstance(_result, pd.DataFrame)
        assert "vlh_business_EV1_ma" in _result
        pd.testing.assert_frame_equal(
            _result[["vlh_business_EV1_ma", "vlh_commute_EV1_ma"]],
            _expected_result[["vlh_business_EV1_ma", "vlh_commute_EV1_ma"]],
        )
