import pytest

from pathlib import Path

import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point, MultiLineString

from tests import test_data
from ra2ce.graph.vector_network_wrapper import VectorNetworkWrapper

_test_dir = test_data / "vector_network_wrapper"
# "region": _test_dir / "_test_polygon.geojson",


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
    def test_init(self, config):
        with pytest.raises(ValueError) as exc_err:
            VectorNetworkWrapper(config=config)
        assert str(exc_err.value) in [
            "Config cannot be None",
            "A network dictionary is required for creating a VectorNetworkWrapper object.",
            'Config["network"] should be a dictionary',
        ]

    def test_parse_ini_value(self, _config_fixture):
        v = VectorNetworkWrapper(_config_fixture)
        assert v._parse_ini_value("a,b,c") == ["a", "b", "c"]
        assert v._parse_ini_value("abc") == "abc"
        assert v._parse_ini_value("") is None

    def test_parse_ini_filename(self, _config_fixture):
        v = VectorNetworkWrapper(_config_fixture)
        file_paths = v._parse_ini_filename("_test_lines.geojson, test.geojson")
        assert file_paths[0].is_file()
        assert not file_paths[1].is_file()

    def test_setup_global(self, _config_fixture):
        v = VectorNetworkWrapper(_config_fixture)
        v._setup_global(_config_fixture)
        assert v.name == "test"
        assert v.region is None
        assert v.crs.to_epsg() == 4326
        assert v.input_path == _test_dir / "static/network"
        assert v.output_path == _test_dir / "output"

    def test_get_network_opt(self, _config_fixture):
        v = VectorNetworkWrapper(_config_fixture)
        network_dict = v._get_network_opt(_config_fixture["network"])
        assert network_dict["files"][0].is_file()
        assert network_dict["file_id"] == "fid"
        assert network_dict["file_crs"].to_epsg() == 4326
        assert network_dict["is_directed"] is False

    def test_read_vector_to_project_region_and_crs(self, _config_fixture):
        v = VectorNetworkWrapper(_config_fixture)
        files = v.network_dict["files"]
        file_crs = v.network_dict["file_crs"]
        vector = v._read_vector_to_project_region_and_crs(files, file_crs)
        assert isinstance(vector, gpd.GeoDataFrame)

    def test_read_vector_to_project_region_and_crs_with_region(self, _config_fixture):
        _config_fixture["project"]["region"] = _test_dir / "_test_polygon.geojson"
        v = VectorNetworkWrapper(_config_fixture)
        files = v.network_dict["files"]
        file_crs = v.network_dict["file_crs"]
        vector = v._read_vector_to_project_region_and_crs(files, file_crs)
        assert vector.crs == v.region.crs
        assert v.region.covers(vector.unary_union).all()

    def test_setup_network_from_vector(self, _config_fixture):
        v = VectorNetworkWrapper(_config_fixture)
        graph, edges = v.setup_network_from_vector()
        assert isinstance(graph, nx.MultiGraph)
        assert isinstance(edges, gpd.GeoDataFrame)

    def test_setup_network_from_vector_with_region(self, _config_fixture):
        _config_fixture["project"]["region"] = _test_dir / "_test_polygon.geojson"
        v = VectorNetworkWrapper(_config_fixture)
        graph, edges = v.setup_network_from_vector()
        assert isinstance(graph, nx.MultiGraph)
        assert isinstance(edges, gpd.GeoDataFrame)

    def test_clean_vector(self, lines_gdf):
        gdf = VectorNetworkWrapper.clean_vector(lines_gdf)
        assert all(gdf.reset_index(drop=True).geom_equals(lines_gdf))

    def test_setup_graph_from_vector(self, lines_gdf):
        graph = VectorNetworkWrapper.setup_graph_from_vector(lines_gdf, False)
        assert graph.nodes(data="geometry") is not None
        assert graph.edges(data="geometry") is not None
        assert graph.graph["crs"] == lines_gdf.crs
        assert isinstance(graph, nx.Graph) and not isinstance(graph, nx.DiGraph)

    def test_setup_network_edges_and_nodes_from_graph(
        self, mock_graph, points_gdf, lines_gdf
    ):
        edges, nodes = VectorNetworkWrapper.setup_network_edges_and_nodes_from_graph(
            mock_graph
        )
        assert edges.geometry.equals(lines_gdf.geometry)
        assert nodes.geometry.equals(points_gdf.geometry)
        assert set(["node_A", "node_B", "edge_fid"]).issubset(edges.columns)
        assert set(["node_fid"]).issubset(nodes.columns)

    def test_explode_and_deduplicate_geometries(self, lines_gdf):
        multi_lines = lines_gdf.geometry.apply(lambda x: MultiLineString([x]))
        gdf = VectorNetworkWrapper.explode_and_deduplicate_geometries(multi_lines)
        assert isinstance(gdf.geometry.iloc[0], LineString)
