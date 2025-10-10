from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pytest
from pyproj import CRS
from shapely.geometry import LineString, MultiLineString, Point

from ra2ce.network.network_config_data.network_config_data import NetworkConfigData
from ra2ce.network.network_wrappers.network_wrapper_protocol import (
    NetworkWrapperProtocol,
)
from ra2ce.network.network_wrappers.vector_network_wrapper import VectorNetworkWrapper
from tests import test_data, test_results

_test_dir = test_data / "vector_network_wrapper"


class TestVectorNetworkWrapper:
    @pytest.fixture
    def points_gdf(self) -> gpd.GeoDataFrame:
        points = [Point(-122.3, 47.6), Point(-122.2, 47.5), Point(-122.1, 47.6)]
        return gpd.GeoDataFrame(geometry=points, crs=4326)

    @pytest.fixture
    def lines_gdf(self) -> gpd.GeoDataFrame:
        points = [Point(-122.3, 47.6), Point(-122.2, 47.5), Point(-122.1, 47.6)]
        lines = [LineString([points[0], points[1]]), LineString([points[1], points[2]])]
        return gpd.GeoDataFrame(geometry=lines, crs=4326)

    @pytest.fixture
    def mock_graph(self):
        points = [(-122.3, 47.6), (-122.2, 47.5), (-122.1, 47.6)]
        lines = [(points[0], points[1]), (points[1], points[2])]

        graph = nx.Graph(crs=4326)
        for point in points:
            graph.add_node(point, geometry=Point(point))
        for line in lines:
            graph.add_edge(
                line[0], line[1], geometry=LineString([Point(line[0]), Point(line[1])])
            )

        return graph

    def test_initialize(self):
        # 1. Define test data.
        _config_data = NetworkConfigData(
            root_path=Path("dummy_path"),
            static_path=Path("dummy_path"),
        )
        _config_data.network.primary_file = Path("dummy_primary")
        _config_data.network.directed = False
        _config_data.origins_destinations.region = Path("dummy_region")

        # 2. Run test.
        _wrapper = VectorNetworkWrapper(_config_data)

        # 3. Verify expectations.
        assert isinstance(_wrapper, VectorNetworkWrapper)
        assert isinstance(_wrapper, NetworkWrapperProtocol)
        assert _wrapper.primary_file == _config_data.network.primary_file
        assert _wrapper.region_path == _config_data.origins_destinations.region
        assert _wrapper.crs.to_epsg() == 4326

    @pytest.fixture
    def _valid_wrapper(self, request: pytest.FixtureRequest) -> VectorNetworkWrapper:
        _network_dir = _test_dir.joinpath("static", "network")
        _config_data = NetworkConfigData()
        _config_data.network.primary_file = _network_dir.joinpath("_test_lines.geojson")
        _config_data.network.directed = False
        _config_data.origins_destinations.region = None
        _config_data.crs = CRS.from_user_input(4326)
        _config_data.static_path = test_results.joinpath(request.node.originalname)
        yield VectorNetworkWrapper(
            config_data=_config_data,
        )

    def test_read_vector_to_project_region_and_crs(
        self, _valid_wrapper: VectorNetworkWrapper
    ):
        # Given
        assert not _valid_wrapper.directed

        # When
        vector = _valid_wrapper._read_vector_to_project_region_and_crs()

        # Then
        assert isinstance(vector, gpd.GeoDataFrame)

    def test_read_vector_to_project_region_and_crs_with_region(
        self, _valid_wrapper: VectorNetworkWrapper
    ):
        # Given
        _valid_wrapper.region_path = _test_dir.joinpath("_test_polygon.geojson")
        _expected_region = gpd.read_file(_valid_wrapper.region_path, engine="pyogrio")
        assert isinstance(_expected_region, gpd.GeoDataFrame)

        # When
        vector = _valid_wrapper._read_vector_to_project_region_and_crs()

        # Then
        assert vector.crs == _expected_region.crs
        assert np.all(_expected_region.geometry.buffer(1e-9).covers(vector.unary_union))

    @pytest.mark.parametrize(
        "region_path",
        [
            pytest.param(None, id="No region"),
            pytest.param(_test_dir / "_test_polygon.geojson", id="With region"),
        ],
    )
    def test_get_network_from_vector(
        self, _valid_wrapper: VectorNetworkWrapper, region_path: Path
    ):
        # Given
        _valid_wrapper.region_path = region_path

        # When
        graph, edges = _valid_wrapper.get_network()

        # Then
        assert isinstance(graph, nx.MultiGraph)
        assert isinstance(edges, gpd.GeoDataFrame)

    def test_clean_vector(self, lines_gdf: gpd.GeoDataFrame):
        # Given
        gdf1 = VectorNetworkWrapper.explode_and_deduplicate_geometries(lines_gdf)

        # When
        gdf2 = VectorNetworkWrapper.clean_vector(
            lines_gdf
        )  # for now cleanup only does the above

        # Then
        assert gdf1.equals(gdf2)

    def test_get_undirected_graph_from_vector(self, lines_gdf: gpd.GeoDataFrame):
        # Given
        _config_data = NetworkConfigData(
            root_path=Path("dummy_path"),
            static_path=Path("dummy_path"),
        )
        _config_data.network.file_id = "dummy_file_id"
        _config_data.network.link_type_column = "dummy_type_column"

        _vector_network_wrapper = VectorNetworkWrapper(_config_data)

        # When
        graph = _vector_network_wrapper._get_undirected_graph_from_vector(lines_gdf, [])

        # Then
        assert graph.nodes(data="geometry") is not None
        assert graph.edges(data="geometry") is not None
        assert graph.graph["crs"] == lines_gdf.crs
        assert isinstance(graph, nx.Graph) and not isinstance(graph, nx.DiGraph)

    def test_get_direct_graph_from_vector(self, lines_gdf: gpd.GeoDataFrame):
        # Given
        _config_data = NetworkConfigData(
            root_path=Path("dummy_path"),
            static_path=Path("dummy_path"),
        )
        _config_data.network.file_id = "dummy_file_id"
        _config_data.network.link_type_column = "dummy_type_column"

        _vector_network_wrapper = VectorNetworkWrapper(_config_data)

        # When
        graph = _vector_network_wrapper._get_direct_graph_from_vector(
            gdf=lines_gdf, edge_attributes_to_include=[]
        )

        # Then
        assert isinstance(graph, nx.DiGraph)

    def test_get_network_edges_and_nodes_from_graph(
        self, mock_graph, points_gdf, lines_gdf
    ):
        # When
        edges, nodes = VectorNetworkWrapper.get_network_edges_and_nodes_from_graph(
            mock_graph
        )

        # Then
        assert edges.geometry.equals(lines_gdf.geometry)
        assert nodes.geometry.equals(points_gdf.geometry)
        assert set(["node_A", "node_B", "edge_fid"]).issubset(edges.columns)
        assert set(["node_fid"]).issubset(nodes.columns)

    def test_explode_and_deduplicate_geometries(self, lines_gdf):
        # Given
        multi_lines = lines_gdf.geometry.apply(lambda x: MultiLineString([x]))

        # When
        gdf = VectorNetworkWrapper.explode_and_deduplicate_geometries(multi_lines)

        # Then
        assert isinstance(gdf.geometry.iloc[0], LineString)
