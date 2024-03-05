from pathlib import Path

import networkx as nx
import pytest
from networkx import Graph, MultiDiGraph
from networkx.utils import graphs_equal
from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry

import ra2ce.network.networks_utils as nut
from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
from ra2ce.network.network_config_data.network_config_data import (
    NetworkConfigData,
    NetworkSection,
)
from ra2ce.network.network_wrappers.network_wrapper_protocol import (
    NetworkWrapperProtocol,
)
from ra2ce.network.network_wrappers.osm_network_wrapper.osm_network_wrapper import (
    OsmNetworkWrapper,
)
from tests import slow_test, test_data, test_results


class TestOsmNetworkWrapper:
    def test_initialize_without_graph_crs(self):
        # 1. Define test data.
        _network_section = NetworkSection(
            network_type=NetworkTypeEnum.ALL,
            road_types=[RoadTypeEnum.PRIMARY],
        )
        _network_config_data = NetworkConfigData(network=_network_section)

        # 2. Run test.
        _wrapper = OsmNetworkWrapper(_network_config_data)

        # 3. Verify final expectations.
        assert isinstance(_wrapper, OsmNetworkWrapper)
        assert isinstance(_wrapper, NetworkWrapperProtocol)
        assert _wrapper.graph_crs.to_epsg() == 4326

    @pytest.fixture
    def _network_wrapper_without_polygon(self) -> OsmNetworkWrapper:
        _network_section = NetworkSection(
            network_type=NetworkTypeEnum.DRIVE,
            road_types=[RoadTypeEnum.ROAD],
            directed=True,
        )
        _output_dir = test_results.joinpath("test_osm_network_wrapper")
        if not _output_dir.exists():
            _output_dir.mkdir(parents=True)
        yield OsmNetworkWrapper(
            NetworkConfigData(network=_network_section, output_path=_output_dir)
        )

    def test_download_clean_graph_from_osm_with_invalid_polygon_arg(
        self, _network_wrapper_without_polygon: OsmNetworkWrapper
    ):
        with pytest.raises(AttributeError) as exc_err:
            _network_wrapper_without_polygon._download_clean_graph_from_osm(
                None,
                _network_wrapper_without_polygon.road_types,
                _network_wrapper_without_polygon.network_type,
            )

        assert str(exc_err.value) == "'NoneType' object has no attribute 'is_valid'"

    def test_download_clean_graph_from_osm_with_invalid_polygon_arg_geometry(
        self, _network_wrapper_without_polygon: OsmNetworkWrapper
    ):
        _polygon = LineString([[0, 0], [1, 0], [1, 1]])
        with pytest.raises(TypeError) as exc_err:
            _network_wrapper_without_polygon._download_clean_graph_from_osm(
                _polygon,
                _network_wrapper_without_polygon.road_types,
                _network_wrapper_without_polygon.network_type,
            )

        assert (
            str(exc_err.value)
            == "Geometry must be a shapely Polygon or MultiPolygon. If you requested graph from place name, make sure your query resolves to a Polygon or MultiPolygon, and not some other geometry, like a Point. See OSMnx documentation for details."
        )

    def test_download_clean_graph_from_osm_with_invalid_network_type_arg(
        self, _network_wrapper_without_polygon: OsmNetworkWrapper
    ):
        _network_type = "drv"
        _polygon = Polygon([(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)])
        with pytest.raises(ValueError) as exc_err:
            _network_wrapper_without_polygon._download_clean_graph_from_osm(
                _polygon, [""], _network_type
            )

            assert str(exc_err.value) == f'Unrecognized network_type "{_network_type}"'

    @pytest.fixture
    def _valid_network_polygon_fixture(self) -> BaseGeometry:
        _test_input_directory = test_data.joinpath("graph", "test_osm_network_wrapper")
        _polygon_file = _test_input_directory.joinpath("_test_polygon.geojson")
        assert _polygon_file.exists()
        yield nut.get_normalized_geojson_polygon(_polygon_file)

    @slow_test
    def test_download_clean_graph_from_osm_output(
        self,
        _network_wrapper_without_polygon: OsmNetworkWrapper,
        _valid_network_polygon_fixture: BaseGeometry,
    ):
        # 1. Define test data.
        _link_type = ""
        _network_type = NetworkTypeEnum.DRIVE

        # 2. Run test.
        graph_complex = _network_wrapper_without_polygon._download_clean_graph_from_osm(
            polygon=_valid_network_polygon_fixture,
            network_type=_network_type.config_value,
            road_types=_link_type,
        )

        # 3. Verify expectations
        # reference: https://www.openstreetmap.org/node/1402598729#map=17/51.98816/4.39126&layers=T
        _osm_id_node_to_validate = 4987298323
        # reference: https://www.openstreetmap.org/way/334316041#map=19/51.98945/4.39166&layers=T
        _osm_id_edge_to_validate = 334316041

        assert isinstance(graph_complex, Graph)
        assert _osm_id_node_to_validate in list(graph_complex.nodes.keys())
        assert _osm_id_edge_to_validate in list(
            map(lambda x: x["osmid"], graph_complex.edges.values())
        )

    def test_get_clean_graph_from_osm_with_invalid_polygon_path_filename(
        self, _network_wrapper_without_polygon: OsmNetworkWrapper
    ):
        _polygon_path = Path("Not_a_valid_path")
        _network_wrapper_without_polygon.polygon_path = _polygon_path
        with pytest.raises(FileNotFoundError) as exc_err:
            _network_wrapper_without_polygon.get_clean_graph_from_osm()

        assert str(exc_err.value) == "No polygon_file file found at {}.".format(
            _polygon_path
        )

    def test_get_clean_graph_from_osm_with_no_polygon_path(
        self, _network_wrapper_without_polygon: OsmNetworkWrapper
    ):
        _network_wrapper_without_polygon.polygon_path = None
        with pytest.raises(ValueError) as exc_err:
            _network_wrapper_without_polygon.get_clean_graph_from_osm()

        assert str(exc_err.value) == "No valid value provided for polygon file."

    @pytest.fixture
    def _valid_graph_fixture(self) -> MultiDiGraph:
        _valid_graph = nx.MultiDiGraph()
        _valid_graph.add_node(1, x=1, y=10)
        _valid_graph.add_node(2, x=2, y=20)
        _valid_graph.add_node(3, x=1, y=10)
        _valid_graph.add_node(4, x=2, y=40)
        _valid_graph.add_node(5, x=3, y=50)

        _valid_graph.add_edge(1, 2, x=[1, 2], y=[10, 20])
        _valid_graph.add_edge(1, 3, x=[1, 1], y=[10, 10])
        _valid_graph.add_edge(2, 4, x=[2, 2], y=[20, 40])
        _valid_graph.add_edge(3, 4, x=[1, 2], y=[10, 40])
        _valid_graph.add_edge(1, 4, x=[1, 2], y=[10, 40])
        _valid_graph.add_edge(5, 3, x=[3, 1], y=[50, 10])
        _valid_graph.add_edge(5, 5, x=[3, 3], y=[50, 50])

        # Add a valid CRS value.
        _valid_graph.graph["crs"] = "EPSG:4326"

        return _valid_graph

    @pytest.fixture
    def _expected_unique_graph_fixture(self) -> MultiDiGraph:
        _valid_unique_graph = nx.MultiDiGraph()
        _valid_unique_graph.add_node(1, x=1, y=10)
        _valid_unique_graph.add_node(2, x=2, y=20)
        _valid_unique_graph.add_node(4, x=2, y=40)
        _valid_unique_graph.add_node(5, x=3, y=50)

        _valid_unique_graph.add_edge(1, 2, x=[1, 2], y=[10, 20])
        _valid_unique_graph.add_edge(2, 4, x=[2, 2], y=[20, 40])
        _valid_unique_graph.add_edge(1, 4, x=[1, 2], y=[10, 40])
        _valid_unique_graph.add_edge(5, 1, x=[3, 1], y=[50, 10])

        return _valid_unique_graph

    def test_drop_duplicates_in_nodes(
        self,
        _valid_graph_fixture: MultiDiGraph,
        _expected_unique_graph_fixture: MultiDiGraph,
    ):
        unique_graph = OsmNetworkWrapper.drop_duplicates_in_nodes(
            graph=_valid_graph_fixture, unique_elements=set()
        )

        assert unique_graph.nodes() == _expected_unique_graph_fixture.nodes()

    @pytest.mark.parametrize(
        "unique_elements",
        [
            pytest.param(None, id="None unique_elements"),
            pytest.param(set(), id="Empty unique_elements"),
            pytest.param({1, 2}, id="Non-tuple elements"),
        ],
    )
    def test_drop_duplicates_in_edges_invalid_unique_elements_input(
        self,
        unique_elements: set,
        _valid_graph_fixture: MultiDiGraph,
        _expected_unique_graph_fixture: MultiDiGraph,
    ):
        with pytest.raises(ValueError) as exc_err:
            OsmNetworkWrapper.drop_duplicates_in_edges(
                graph=_valid_graph_fixture,
                unique_elements=unique_elements,
                unique_graph=None,
            )

        assert (
            str(exc_err.value)
            == """unique_elements cannot be None, empty, or have non-tuple elements. 
            Provide a set with all unique node coordinates as tuples of (x, y)"""
        )

    def test_drop_duplicates_in_edges_invalid_unique_graph_input(
        self,
        _valid_graph_fixture: MultiDiGraph,
        _expected_unique_graph_fixture: MultiDiGraph,
    ):
        with pytest.raises(ValueError) as exc_err:
            OsmNetworkWrapper.drop_duplicates_in_edges(
                graph=_valid_graph_fixture, unique_elements={(1, 2)}, unique_graph=None
            )

        assert (
            str(exc_err.value)
            == """unique_graph cannot be None. Provide a graph with unique nodes or perform the 
        drop_duplicates_in_nodes on the graph to generate a unique_graph"""
        )

    def test_drop_duplicates_in_edges(
        self,
        _valid_graph_fixture: MultiDiGraph,
        _expected_unique_graph_fixture: MultiDiGraph,
    ):
        # 1. Define test data.
        unique_elements = {(1, 10), (2, 20), (4, 40), (5, 50)}

        unique_graph = nx.MultiDiGraph()
        unique_graph.add_node(1, x=1, y=10)
        unique_graph.add_node(2, x=2, y=20)
        unique_graph.add_node(4, x=2, y=40)
        unique_graph.add_node(5, x=3, y=50)

        # 2. Run test.
        unique_graph = OsmNetworkWrapper.drop_duplicates_in_edges(
            graph=_valid_graph_fixture,
            unique_elements=unique_elements,
            unique_graph=unique_graph,
        )

        # 3. Verify results
        assert graphs_equal(unique_graph, _expected_unique_graph_fixture)

    def test_snap_nodes_to_nodes(self, _valid_graph_fixture: MultiDiGraph):
        # 1. Define test data.
        _threshold = 0.00002

        # 2. Run test.
        _result_graph = OsmNetworkWrapper.snap_nodes_to_nodes(
            _valid_graph_fixture, _threshold
        )

        # 3. Verify expectations.
        assert isinstance(_result_graph, MultiDiGraph)
