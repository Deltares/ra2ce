from pathlib import Path

import networkx as nx
import pytest
from geopandas import GeoDataFrame
from networkx import Graph, MultiDiGraph, MultiGraph
from networkx.utils import graphs_equal
from shapely import wkt
from shapely.geometry import LineString, Point, Polygon
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

    @staticmethod
    def _get_dummy_network_config_data() -> NetworkConfigData:
        _network_section = NetworkSection(
            network_type=NetworkTypeEnum.DRIVE,
            road_types=[RoadTypeEnum.ROAD],
            directed=True,
        )
        _output_dir = test_results.joinpath("test_osm_network_wrapper")
        if not _output_dir.exists():
            _output_dir.mkdir(parents=True)
        return NetworkConfigData(network=_network_section, output_path=_output_dir)

    @pytest.fixture
    def _network_wrapper_without_polygon(self) -> OsmNetworkWrapper:
        yield OsmNetworkWrapper(self._get_dummy_network_config_data())

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

    @pytest.mark.parametrize(
        "road_types",
        [pytest.param(None, id="With None"), pytest.param([], id="With empty list")],
    )
    def test_download_clean_graph_from_osm_with_invalid_network_type_arg(
        self,
        road_types: list | None,
        _network_wrapper_without_polygon: OsmNetworkWrapper,
    ):
        _network_type = NetworkTypeEnum.DRIVE
        _polygon = Polygon([(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)])
        with pytest.raises(ValueError) as exc_err:
            _network_wrapper_without_polygon._download_clean_graph_from_osm(
                _polygon, road_types, _network_type
            )

            assert (
                str(exc_err.value)
                == f'Unrecognized network_type "{_network_type.config_value}"'
            )

    @pytest.fixture
    def _valid_network_polygon_fixture(self) -> BaseGeometry:
        _test_input_directory = test_data.joinpath(
            "network", "test_osm_network_wrapper"
        )
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
        _link_type = []
        _network_type = NetworkTypeEnum.DRIVE

        # 2. Run test.
        graph_complex = _network_wrapper_without_polygon._download_clean_graph_from_osm(
            polygon=_valid_network_polygon_fixture,
            network_type=_network_type,
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

    @pytest.mark.parametrize(
        "polygon_path",
        [
            pytest.param(Path("Not_a_valid_path"), id="Not a valid path"),
            pytest.param(None, id="Path is None"),
        ],
    )
    def test_get_clean_graph_from_osm_with_invalid_polygon_path(
        self, _network_wrapper_without_polygon: OsmNetworkWrapper, polygon_path: Path
    ):
        _result = _network_wrapper_without_polygon._get_clean_graph_from_osm(
            polygon_path
        )

        assert _result is None

    @pytest.fixture
    def _graph_fixture_node_to_edge(self) -> MultiDiGraph:
        _graph = nx.MultiDiGraph()
        _graph.add_node(1, x=2, y=10, pos=(2, 10))
        _graph.add_node(2, x=2, y=20, pos=(2, 20))
        _graph.add_node(3, x=2.1, y=15, pos=(2.1, 15))
        _graph.add_node(4, x=4, y=15, pos=(4, 15))

        _graph.add_edge(1, 2, length=10)
        _graph.add_edge(3, 4, length=1.9)

        _graph.graph["crs"] = "EPSG:4326"

        return _graph

    @pytest.fixture
    def _valid_graph_fixture_node_to_edge(self) -> MultiDiGraph:
        _valid_graph = nx.MultiDiGraph()
        _valid_graph.add_node(1, x=2, y=10, pos=(2, 10))
        _valid_graph.add_node(2, x=2, y=20, pos=(2, 20))
        _valid_graph.add_node(3, x=2.1, y=15, pos=(2.1, 15))
        _valid_graph.add_node(4, x=4, y=15, pos=(4, 15))

        _valid_graph.add_edge(1, 2, length=10)
        _valid_graph.add_edge(3, 4, length=1.9)

        _valid_graph.graph["crs"] = "EPSG:4326"

        return _valid_graph

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

    def test_snap_nodes_to_edges(self, _graph_fixture_node_to_edge: MultiDiGraph):

        # 1. Define test data.
        _threshold = 0.1

        # 2. Run test.
        _result_graph = OsmNetworkWrapper.snap_nodes_to_edges(
            _graph_fixture_node_to_edge, _threshold
        )
        for node, data in _result_graph.nodes(data=True):
            pos = (data["x"], data["y"])  # Get the (x, y) position tuple
            _result_graph.nodes[node]["pos"] = pos
            _result_graph.nodes[node]["geometry"] = Point(data["x"], data["y"])

        # 3. Verify expectations.
        _valid_graph = nx.MultiDiGraph()
        _valid_graph.add_node(1, x=2, y=10, pos=(2, 10))
        _valid_graph.add_node(2, x=2, y=20, pos=(2, 20))
        _valid_graph.add_node(4, x=4, y=15, pos=(4, 15))
        _valid_graph.add_node(3, x=2, y=15, pos=(2, 15))

        _valid_graph.add_edge(1, 3, length=553135.0)
        _valid_graph.add_edge(3, 2, length=553377.0)
        _valid_graph.add_edge(3, 4, length=215100.0)

        _valid_graph.graph["crs"] = "EPSG:4326"

        for node, data in _valid_graph.nodes(data=True):
            _valid_graph.nodes[node]["geometry"] = Point(data["x"], data["y"])

        for u, v, key, data in _valid_graph.edges(keys=True, data=True):
            u_geom = _valid_graph.nodes[u]["geometry"]
            v_geom = _valid_graph.nodes[v]["geometry"]
            edge_geometry = LineString([u_geom, v_geom])
            data["geometry"] = edge_geometry

        result_edges_wkt = sorted(
            [
                (u, v, k, wkt.dumps(data["geometry"]))
                for u, v, k, data in _result_graph.edges(keys=True, data=True)
            ]
        )
        valid_edges_wkt = sorted(
            [
                (u, v, k, wkt.dumps(data["geometry"]))
                for u, v, k, data in _valid_graph.edges(keys=True, data=True)
            ]
        )

        assert isinstance(_result_graph, MultiDiGraph)
        assert _result_graph.nodes(data=True) == _valid_graph.nodes(data=True)
        assert result_edges_wkt == valid_edges_wkt

    @slow_test
    def test_given_valid_base_geometry_with_polygon(
        self, _valid_network_polygon_fixture: BaseGeometry
    ):
        # 1. Define test data.
        _network_config_data = self._get_dummy_network_config_data()
        _network_config_data.network.network_type = NetworkTypeEnum.DRIVE
        _network_config_data.network.road_types = []

        # 2. Run test.
        _wrapper = OsmNetworkWrapper.with_polygon(
            _network_config_data, _valid_network_polygon_fixture
        )

        # 3. Verify expectations.
        assert isinstance(_wrapper, OsmNetworkWrapper)
        assert isinstance(_wrapper.polygon_graph, MultiDiGraph)

    @slow_test
    def test_given_no_output_graph_dir_when_get_network(self):
        # 1. Define test data.
        _test_input_directory = test_data.joinpath(
            "network", "test_osm_network_wrapper"
        )
        _polygon_file = _test_input_directory.joinpath("_test_polygon.geojson")
        assert _polygon_file.exists()

        _network_config_data = self._get_dummy_network_config_data()
        _network_config_data.network.polygon = _polygon_file
        _network_config_data.network.network_type = NetworkTypeEnum.DRIVE
        _network_config_data.network.road_types = []
        # `output_graph_dir` is a property indirectly derived from `static_path`.
        _network_config_data.static_path = None

        # 2. Run test.
        _wrapper = OsmNetworkWrapper(_network_config_data)
        _result_mg, _result_gdf = _wrapper.get_network()

        # 3. Verify expectations.
        assert isinstance(_wrapper, OsmNetworkWrapper)
        assert isinstance(_wrapper.polygon_graph, MultiDiGraph)
        assert isinstance(_result_mg, MultiGraph)
        assert isinstance(_result_gdf, GeoDataFrame)

    @slow_test
    def test_get_network_from_polygon_with_valid_data(
        self, _valid_network_polygon_fixture: BaseGeometry
    ):
        # 1. Define test data.
        _network_config_data = self._get_dummy_network_config_data()
        _network_config_data.network.network_type = NetworkTypeEnum.DRIVE
        _network_config_data.network.road_types = []

        # 2. Run test.
        _network_tuple = OsmNetworkWrapper.get_network_from_polygon(
            _network_config_data, _valid_network_polygon_fixture
        )

        # 3. Verify expectations.
        assert isinstance(_network_tuple, tuple)

        _result_graph, _result_gdf = _network_tuple
        assert isinstance(_result_graph, MultiGraph)
        assert isinstance(_result_gdf, GeoDataFrame)

    @pytest.mark.parametrize(
        "polygon_path", [pytest.param(None), pytest.param("not_a_valid_path")]
    )
    def test_get_network_from_geojson_without_path_raises(self, polygon_path: Path):
        # 1. Define test data
        _config_data = NetworkConfigData()
        _config_data.network.polygon = polygon_path

        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            OsmNetworkWrapper.get_network_from_geojson(_config_data)

        # 3. Verify expectations.
        assert (
            str(exc_err.value)
            == "A valid network polygon (.geojson) file path needs to be provided."
        )

    @slow_test
    def test_get_network_from_geojson_with_valid_data(self):
        # 1. Define test data
        _test_input_directory = test_data.joinpath(
            "network", "test_osm_network_wrapper"
        )
        _polygon_file = _test_input_directory.joinpath("_test_polygon.geojson")
        assert _polygon_file.exists()

        _config_data = NetworkConfigData()
        _config_data.network.polygon = _polygon_file
        _config_data.network.network_type = NetworkTypeEnum.DRIVE
        _config_data.network.road_types = []

        # 2. Run test.
        _network_tuple = OsmNetworkWrapper.get_network_from_geojson(_config_data)

        # 3. Verify expectations
        assert isinstance(_network_tuple, tuple)

        _result_graph, _result_gdf = _network_tuple
        assert isinstance(_result_graph, MultiGraph)
        assert isinstance(_result_gdf, GeoDataFrame)
