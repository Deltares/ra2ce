import shutil
from pathlib import Path
from typing import Iterator

import geopandas as gpd
import networkx as nx
import pytest

from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_config_data.network_config_data_reader import (
    NetworkConfigDataReader,
)
from ra2ce.network.networks import Network
from tests import slow_test, test_data, test_results

# Just to make sonar-cloud stop complaining.
_network_ini_name = "network.ini"
_base_graph_p_filename = "base_graph.p"
_base_network_feather_filename = "base_network.feather"


class TestNetworks:
    def test_initialize(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _test_dir = test_results / "test_networks" / request.node.name
        _config_data = NetworkConfigData(
            static_path=_test_dir.joinpath("static"),
        )
        _files = {}

        if _test_dir.exists():
            shutil.rmtree(_test_dir)

        # 2. Run test.
        _network = Network(_config_data, _files)

        # 3. Verify expectations
        assert isinstance(_network, Network)

    @pytest.fixture(autouse=False)
    def case_data_dir(self, request: pytest.FixtureRequest) -> Iterator[Path]:
        _test_data_dir = test_data / request.param
        _output_files_dir = _test_data_dir / "output"
        _output_graph_dir = _test_data_dir / "static" / "output_graph"

        def purge_output_dirs():
            shutil.rmtree(_output_files_dir, ignore_errors=True)
            shutil.rmtree(_output_graph_dir, ignore_errors=True)

        purge_output_dirs()
        yield _test_data_dir
        purge_output_dirs()

    @slow_test
    @pytest.mark.parametrize(
        "case_data_dir, expected_files",
        [
            pytest.param(
                "1_network_shape",
                [_base_graph_p_filename, _base_network_feather_filename],
                id="Case 1. Network creation from shp file",
            ),
            pytest.param(
                "2_network_shape",
                [_base_graph_p_filename, _base_network_feather_filename],
                id="Case 2. Merges lines and cuts lines at the intersections",
            ),
            pytest.param(
                "3_network_osm_download",
                [
                    _base_graph_p_filename,
                    _base_network_feather_filename,
                    "simple_to_complex.json",
                    "complex_to_simple.json",
                ],
                id="Case 3. OSM download",
            ),
        ],
        indirect=["case_data_dir"],
    )
    def test_network_creation(
        self,
        case_data_dir: Path,
        expected_files: list[str],
        request: pytest.FixtureRequest,
    ):
        """To test the graph and network creation from a shapefile. Also applies line segmentation for the network."""
        # 1. Given test data.
        _test_dir = test_results.joinpath("test_networks", request.node.name)

        network_ini = case_data_dir.joinpath(_network_ini_name)
        assert network_ini.is_file()

        _config_data = NetworkConfigDataReader().read(network_ini)
        _config_data.output_path = _test_dir.joinpath("output")
        _config_data.static_path = case_data_dir.joinpath("static")
        _output_graph_dir = case_data_dir.joinpath("static", "output_graph")
        _graph_files = GraphFilesCollection()

        # 2. When run test.
        _network_controller = Network(_config_data, _graph_files).create()

        # 3. Then verify expectations.
        def validate_file(filename: str):
            _graph_file = _output_graph_dir.joinpath(filename)
            return _graph_file.is_file() and _graph_file.exists()

        assert isinstance(_network_controller, GraphFilesCollection)
        assert isinstance(_network_controller.base_graph.graph, nx.MultiGraph)
        assert isinstance(_network_controller.base_network.graph, gpd.GeoDataFrame)
        assert _network_controller.origins_destinations_graph.graph is None
        assert all(map(validate_file, expected_files))
