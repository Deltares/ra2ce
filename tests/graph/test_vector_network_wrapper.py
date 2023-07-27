import pytest

import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point, MultiLineString

from tests import test_data
from ra2ce.graph.shp_network_wrapper.vector_network_wrapper import VectorNetworkWrapper

_test_dir = test_data / "vector_network_wrapper"


class TestVectorNetworkWrapper:
    @pytest.fixture
    def _config_fixture(self) -> dict:
        yield {
            "project": {
                "name": "test",
                "crs": 4326,
            },
            "network": {
                "directed": False,
                "source": "shapefile",
                "primary_file": "_test_lines.geojson",
                "diversion_file": None,
                "file_id": "fid",
                "polygon": None,
                "network_type": None,
                "road_types": None,
                "save_shp": False,
            },
            "static": _test_dir / "static",
            "output": _test_dir / "output",
        }

    @pytest.fixture
    def points_gdf(self):
        points = [Point(-122.3, 47.6), Point(-122.2, 47.5), Point(-122.1, 47.6)]
        return gpd.GeoDataFrame(geometry=points, crs=4326)

    @pytest.fixture
    def lines_gdf(self):
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

    @pytest.mark.parametrize(
        "config",
        [
            pytest.param(None, id="NONE as dictionary"),
            pytest.param({}, id="Empty dictionary"),
            pytest.param({"network": {}}, id='Empty "network" in Config'),
            pytest.param({"network": "string"}, id='Invalid "network" type in Config'),
        ],
    )
    def test_init(self, config: dict):
        with pytest.raises(ValueError) as exc_err:
            VectorNetworkWrapper(config=config)
        assert str(exc_err.value) in [
            "Config cannot be None",
            "A network dictionary is required for creating a VectorNetworkWrapper object.",
            'Config["network"] should be a dictionary',
        ]

    def test_parse_ini_stringlist_with_comma_separated_string(self, _config_fixture):
        # Given
        test_wrapper = VectorNetworkWrapper(_config_fixture)
        ini_value = "a,b,c"

        # When
        result = test_wrapper._parse_ini_stringlist(ini_value)

        # Then
        assert result == ["a", "b", "c"]

    def test_parse_ini_stringlist_with_single_string(self, _config_fixture):
        # Given
        test_wrapper = VectorNetworkWrapper(_config_fixture)
        ini_value = "abc"

        # When
        result = test_wrapper._parse_ini_stringlist(ini_value)

        # Then
        assert result == "abc"

    def test_parse_ini_stringlist_with_empty_string(self, _config_fixture):
        # Given
        test_wrapper = VectorNetworkWrapper(_config_fixture)
        ini_value = ""

        # When
        result = test_wrapper._parse_ini_stringlist(ini_value)

        # Then
        assert result is None

    def test_parse_ini_filenamelist(self, _config_fixture):
        # Given
        test_wrapper = VectorNetworkWrapper(_config_fixture)
        ini_value = "_test_lines.geojson, dummy.geojson"

        # When
        file_paths = test_wrapper._parse_ini_filenamelist(ini_value)

        # Then
        assert file_paths[0].is_file()

    def test_setup_global(self, _config_fixture):
        test_wrapper = VectorNetworkWrapper(_config_fixture)
        test_wrapper._setup_global(_config_fixture)
        assert test_wrapper.name == "test"
        assert test_wrapper.region is None
        assert test_wrapper.crs.to_epsg() == 4326
        assert test_wrapper.input_path == _test_dir / "static/network"
        assert test_wrapper.output_path == _test_dir / "output"

    def test_get_network_opt(self, _config_fixture):
        test_wrapper = VectorNetworkWrapper(_config_fixture)
        network_dict = test_wrapper._get_network_opt(_config_fixture["network"])
        assert network_dict["files"][0].is_file()
        assert network_dict["file_id"] == "fid"
        assert network_dict["file_crs"].to_epsg() == 4326
        assert network_dict["is_directed"] is False

    def test_read_vector_to_project_region_and_crs(self, _config_fixture):
        # Given
        test_wrapper = VectorNetworkWrapper(_config_fixture)
        files = test_wrapper.network_dict["files"]
        file_crs = test_wrapper.network_dict["file_crs"]

        # When
        vector = test_wrapper._read_vector_to_project_region_and_crs(files, file_crs)

        # Then
        assert isinstance(vector, gpd.GeoDataFrame)

    def test_read_vector_to_project_region_and_crs_with_region(self, _config_fixture):
        # Given
        _config_fixture["project"]["region"] = _test_dir / "_test_polygon.geojson"
        test_wrapper = VectorNetworkWrapper(_config_fixture)
        files = test_wrapper.network_dict["files"]
        file_crs = test_wrapper.network_dict["file_crs"]

        # When
        vector = test_wrapper._read_vector_to_project_region_and_crs(files, file_crs)

        # Then
        assert vector.crs == test_wrapper.region.crs
        assert test_wrapper.region.covers(vector.unary_union).all()

    def test_setup_network_from_vector(self, _config_fixture):
        # Given
        test_wrapper = VectorNetworkWrapper(_config_fixture)

        # When
        graph, edges = test_wrapper.get_network_from_vector()

        # Then
        assert isinstance(graph, nx.MultiGraph)
        assert isinstance(edges, gpd.GeoDataFrame)

    def test_setup_network_from_vector_with_region(self, _config_fixture):
        # Given
        _config_fixture["project"]["region"] = _test_dir / "_test_polygon.geojson"
        test_wrapper = VectorNetworkWrapper(_config_fixture)

        # When
        graph, edges = test_wrapper.get_network_from_vector()

        # Then
        assert isinstance(graph, nx.MultiGraph)
        assert isinstance(edges, gpd.GeoDataFrame)

    def test_clean_vector(self, lines_gdf):
        # Given
        gdf1 = VectorNetworkWrapper.explode_and_deduplicate_geometries(lines_gdf)

        # When
        gdf2 = VectorNetworkWrapper.clean_vector(
            lines_gdf
        )  # for now cleanup only does the above

        # Then
        assert gdf1.equals(gdf2)

    def test_setup_graph_from_vector(self, lines_gdf):
        # When
        graph = VectorNetworkWrapper.setup_graph_from_vector(lines_gdf)

        # Then
        assert graph.nodes(data="geometry") is not None
        assert graph.edges(data="geometry") is not None
        assert graph.graph["crs"] == lines_gdf.crs
        assert isinstance(graph, nx.Graph) and not isinstance(graph, nx.DiGraph)

    def test_setup_digraph_from_vector(self, lines_gdf):
        # When
        graph = VectorNetworkWrapper.setup_digraph_from_vector(lines_gdf)

        # Then
        assert isinstance(graph, nx.DiGraph)

    def test_setup_network_edges_and_nodes_from_graph(
        self, mock_graph, points_gdf, lines_gdf
    ):
        # When
        edges, nodes = VectorNetworkWrapper.setup_network_edges_and_nodes_from_graph(
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
