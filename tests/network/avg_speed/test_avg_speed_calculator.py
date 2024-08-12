from pathlib import Path
from typing import Iterator

import networkx as nx
import pytest

from ra2ce.network.avg_speed.avg_speed_calculator import AvgSpeedCalculator
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from tests import test_results

_SPEED_SECONDARY = 80.0
_SPEED_TERTIARY = 30.0
_SPEED_DEFAULT = 50.0


class TestAvgSpeedCalculator:
    @pytest.fixture(name="valid_network")
    def _get_valid_network(self) -> Iterator[nx.MultiGraph]:
        _graph = nx.MultiGraph()
        _graph.add_nodes_from([1, 2, 3, 4])
        _graph.add_edge(
            1,
            2,
            key=1,
            highway="tertiary",
            maxspeed=str(round(_SPEED_TERTIARY)),
            length=1000.0,
        )
        _graph.add_edge(2, 3, key=2, highway="tertiary", length=2000.0)
        _graph.add_edge(3, 4, key=3, highway="tertiary_link", length=3500.0)
        _graph.add_edge(
            1,
            3,
            key=4,
            highway="secondary",
            maxspeed=str(round(_SPEED_SECONDARY)),
            length=2200.0,
        )
        _graph.add_edge(1, 4, key=5, highway="['primary', 'tertiary']", length=5000.0)
        yield _graph

    def test_initialize(self, valid_network: nx.MultiGraph):
        # 1. Run test
        _calculator = AvgSpeedCalculator(valid_network, "highway", None)

        # 2. Verify expectations
        assert isinstance(_calculator, AvgSpeedCalculator)

    @pytest.mark.parametrize(
        "speed, expected",
        [
            pytest.param("", 0.0, id="Empty string"),
            pytest.param("a60", 0.0, id="Invalid string"),
            pytest.param("60", 60.0, id="Single string"),
            pytest.param(["60", "50"], 55.0, id="List of strings"),
            pytest.param("60;50", 55.0, id="; as separator"),
            pytest.param("60-50", 55.0, id="- as separator"),
            pytest.param("60|50", 55.0, id="| as separator"),
            pytest.param("50 mph", 80.4672, id="Mph string"),
        ],
    )
    def test_parse_speed(self, speed: str, expected: float):
        # 1. Run test
        _result = AvgSpeedCalculator.parse_speed(speed)

        # 2. Verify expectations
        assert _result == pytest.approx(expected)

    def test_calculate_without_output_dir(self, valid_network: nx.MultiGraph):
        # 1. Run test
        _calculator = AvgSpeedCalculator(valid_network, "highway", None)

        # 2. Verify expectations
        assert _calculator.avg_speed is not None
        assert (
            _calculator.avg_speed.get_avg_speed([RoadTypeEnum.SECONDARY])
            == _SPEED_SECONDARY
        )
        assert (
            _calculator.avg_speed.get_avg_speed([RoadTypeEnum.TERTIARY])
            == _SPEED_TERTIARY
        )
        assert (
            _calculator.avg_speed.get_avg_speed([RoadTypeEnum.TERTIARY_LINK])
            == _SPEED_TERTIARY
        )
        assert (
            _calculator.avg_speed.get_avg_speed(
                [RoadTypeEnum.PRIMARY, RoadTypeEnum.TERTIARY]
            )
            == _SPEED_TERTIARY
        )
        assert (
            _calculator.avg_speed.get_avg_speed([RoadTypeEnum.INVALID])
            == _SPEED_DEFAULT
        )

    def test_calculate_with_empty_output_dir_creates_csv(
        self, valid_network: nx.MultiGraph, request: pytest.FixtureRequest
    ):
        # 1. Define test data
        _csv_dir = test_results.joinpath(request.node.name)
        _csv_path = _csv_dir.joinpath("avg_speed.csv")
        _csv_path.unlink(missing_ok=True)

        # 2. Run test
        _calculator = AvgSpeedCalculator(valid_network, "highway", _csv_dir)

        # 3. Verify expectations
        assert _csv_path.is_file()

    def test_calculate_with_csv_in_output_dir_reads_csv(
        self, valid_network: nx.MultiGraph, avg_speed_csv: Path
    ):
        # 1. Define test data
        assert avg_speed_csv.is_file()

        # 2. Run test
        _calculator = AvgSpeedCalculator(valid_network, "highway", avg_speed_csv.parent)

        # 3. Verify expectations
        assert len(_calculator.avg_speed.road_types) > 0

    def test_assign(self, valid_network: nx.MultiGraph):
        # 1. Define test data
        _calculator = AvgSpeedCalculator(valid_network, "highway", None)

        # 2. Run test
        _calculator.assign()

        # 3. Verify expectations
        _avg_speed_key = "avgspeed"
        _time_key = "time"
        assert _calculator.graph.edges[1, 2, 1][_avg_speed_key] == _SPEED_TERTIARY
        assert _calculator.graph.edges[1, 2, 1][_time_key] == pytest.approx(0.033)
        assert _calculator.graph.edges[2, 3, 2][_avg_speed_key] == _SPEED_TERTIARY
        assert _calculator.graph.edges[2, 3, 2][_time_key] == pytest.approx(0.067)
        assert _calculator.graph.edges[3, 4, 3][_avg_speed_key] == _SPEED_TERTIARY
        assert _calculator.graph.edges[3, 4, 3][_time_key] == pytest.approx(0.117)
        assert _calculator.graph.edges[1, 3, 4][_avg_speed_key] == _SPEED_SECONDARY
        assert _calculator.graph.edges[1, 3, 4][_time_key] == pytest.approx(0.028)
        assert _calculator.graph.edges[1, 4, 5][_avg_speed_key] == _SPEED_TERTIARY
        assert _calculator.graph.edges[1, 4, 5][_time_key] == pytest.approx(0.167)
