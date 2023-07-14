import shutil
from pathlib import Path

import pytest
from networkx import Graph
from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry

from ra2ce.graph.networks import Network
from tests import test_results, slow_test, test_data
import ra2ce.graph.networks_utils as nut


class TestNetworks:
    def test_initialize(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _test_dir = test_results / "test_networks" / request.node.name
        _config = {
            "static": _test_dir / "static",
            "origins_destinations": {
                "origins": None,
                "destinations": None,
                "origins_names": None,
                "destinations_names": None,
                "id_name_origin_destination": None,
                "category": "dummy_category",
                "region": "",
            },
            "cleanup": {"snapping_threshold": None, "segmentation_length": None},
        }
        _files = []

        if _test_dir.exists():
            shutil.rmtree(_test_dir)

        # 2. Run test.
        _network = Network(_config, _files)

        # 3. Verify expectations
        assert isinstance(_network, Network)
        assert _network.od_category == "dummy_category"

    def test_initialize_without_category(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _test_dir = test_results / "test_networks" / request.node.name
        _config = {
            "static": _test_dir / "static",
            "origins_destinations": {
                "origins": None,
                "destinations": None,
                "origins_names": None,
                "destinations_names": None,
                "id_name_origin_destination": None,
                "region": "",
            },
            "cleanup": {"snapping_threshold": None, "segmentation_length": None},
        }
        _files = []

        if _test_dir.exists():
            shutil.rmtree(_test_dir)

        # 2. Run test.
        _network = Network(_config, _files)

        # 3. Verify expectations
        assert isinstance(_network, Network)

    def test_get_graph_from_osm_download_with_invalid_polygon_arg(self):
        _polygon = None
        _link_type = ""
        _network_type = ""
        with pytest.raises(AttributeError) as exc_err:
            Network.get_graph_from_osm_download(_polygon, _link_type, _network_type)

        assert str(exc_err.value) == "'NoneType' object has no attribute 'is_valid'"

    def test_get_graph_from_osm_download_with_invalid_polygon_arg_geometry(self):
        _polygon = LineString([[0, 0], [1, 0], [1, 1]])
        _link_type = ""
        _network_type = ""
        with pytest.raises(TypeError) as exc_err:
            Network.get_graph_from_osm_download(_polygon, _link_type, _network_type)

        assert str(
            exc_err.value) == "Geometry must be a shapely Polygon or MultiPolygon. If you requested graph from place name, make sure your query resolves to a Polygon or MultiPolygon, and not some other geometry, like a Point. See OSMnx documentation for details."

    def test_get_graph_from_osm_download_with_invalid_network_type_arg(self):
        _polygon = Polygon([(0., 0.), (0., 1.), (1., 1.), (1., 0.), (0., 0.)])
        _link_type = ""
        _network_type = ""
        with pytest.raises(ValueError) as exc_err:
            Network.get_graph_from_osm_download(_polygon, _link_type, _network_type)

        assert str(exc_err.value) == 'Unrecognized network_type ""'

    @pytest.fixture
    def valid_network_polygon(self) -> BaseGeometry:
        _test_input_directory = test_data.joinpath("graph", "test_networks")
        _polygon_file = _test_input_directory.joinpath("_test_polygon.geojson")
        assert _polygon_file.exists()
        _polygon_dict = nut.read_geojson(_polygon_file)
        yield nut.geojson_to_shp(_polygon_dict)

    @slow_test
    def test_get_graph_from_osm_download_output(self, valid_network_polygon: BaseGeometry):
        # 1. Define test data.
        _link_type = ""
        _network_type = "drive"

        # 2. Run test.
        graph_complex = Network.get_graph_from_osm_download(
            polygon=valid_network_polygon,
            network_type=_network_type,
            link_type=_link_type
        )

        # 3. Verify expectations
        # reference: https://www.openstreetmap.org/node/1402598729#map=17/51.98816/4.39126&layers=T
        _osm_id_node_to_validate = 4987298323
        # reference: https://www.openstreetmap.org/way/334316041#map=19/51.98945/4.39166&layers=T
        _osm_id_edge_to_validate = 334316041

        assert isinstance(graph_complex, Graph)
        assert _osm_id_node_to_validate in list(graph_complex.nodes.keys())
        assert _osm_id_edge_to_validate in list(map(lambda x: x["osmid"], graph_complex.edges.values()))
