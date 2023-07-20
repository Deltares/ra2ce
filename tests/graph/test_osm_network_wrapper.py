import shutil
from pathlib import Path

import pytest
from networkx import Graph
from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry

from tests import test_data, slow_test
import ra2ce.graph.networks_utils as nut
from ra2ce.graph.osm_network_wrapper import OsmNetworkWrapper


class TestOsmNetworkWrapper:
    @pytest.fixture
    def _config_fixture(self) -> dict:
        _test_dir = test_data / "graph" / "test_osm_network_wrapper"

        yield {
            "static": _test_dir / "static",
            "network": {
                "polygon": "_test_polygon.geojson"
            },
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

    @pytest.mark.parametrize("config", [
        pytest.param(None, id="NONE as dictionary"),
        pytest.param({}, id="Empty dictionary"),
        pytest.param({"network": {}}, id='"Empty Config["network"]"'),
        pytest.param({"network": "string"}, id='"invalid Config["network"] type"')
    ])
    def test_osm_network_wrapper_initialisation_with_invalid_config(self, config: dict):
        _files = []
        with pytest.raises(ValueError) as exc_err:
            OsmNetworkWrapper(config=config)
        assert str(exc_err.value) == "Config cannot be None" or \
               "A network dictionary is required for creating a OsmNetworkWrapper object" or \
               'Config["network"] should be a dictionary'

    def test_get_graph_from_osm_download_with_invalid_polygon_arg(self, _config_fixture: dict):
        _files = []
        # _network = Network(_config_fixture, _files)
        _osm_network = OsmNetworkWrapper(config=_config_fixture)
        _polygon = None
        _link_type = ""
        _network_type = ""
        with pytest.raises(AttributeError) as exc_err:
            _osm_network.get_graph_from_osm_download(_polygon, _link_type, _network_type)

        assert str(exc_err.value) == "'NoneType' object has no attribute 'is_valid'"

    def test_get_graph_from_osm_download_with_invalid_polygon_arg_geometry(self, _config_fixture: dict):
        _osm_network = OsmNetworkWrapper(config=_config_fixture)
        _polygon = LineString([[0, 0], [1, 0], [1, 1]])
        _link_type = ""
        _network_type = ""
        with pytest.raises(TypeError) as exc_err:
            _osm_network.get_graph_from_osm_download(_polygon, _link_type, _network_type)

        assert str(
            exc_err.value) == "Geometry must be a shapely Polygon or MultiPolygon. If you requested graph from place name, make sure your query resolves to a Polygon or MultiPolygon, and not some other geometry, like a Point. See OSMnx documentation for details."

    def test_get_graph_from_osm_download_with_invalid_network_type_arg(self, _config_fixture: dict):
        _osm_network = OsmNetworkWrapper(config=_config_fixture)
        _polygon = Polygon([(0., 0.), (0., 1.), (1., 1.), (1., 0.), (0., 0.)])
        _link_type = ""
        _network_type = ""
        with pytest.raises(ValueError) as exc_err:
            _osm_network.get_graph_from_osm_download(_polygon, _link_type, _network_type)

        assert str(exc_err.value) == 'Unrecognized network_type ""'

    @pytest.fixture
    def valid_network_polygon(self) -> BaseGeometry:
        _test_input_directory = test_data.joinpath("graph", "test_osm_network_wrapper")
        _polygon_file = _test_input_directory.joinpath("_test_polygon.geojson")
        assert _polygon_file.exists()
        _polygon_dict = nut.read_geojson(_polygon_file)
        yield nut.geojson_to_shp(_polygon_dict)

    @slow_test
    def test_get_graph_from_osm_download_output(self, _config_fixture: dict, valid_network_polygon: BaseGeometry):
        # 1. Define test data.
        _osm_network = OsmNetworkWrapper(config=_config_fixture)
        _link_type = ""
        _network_type = "drive"

        # 2. Run test.
        graph_complex = _osm_network.get_graph_from_osm_download(
            polygon=valid_network_polygon,
            network_type=_network_type,
            link_type=_link_type
        )
        _osm_network.drop_duplicates(graph_complex)

        # 3. Verify expectations
        # reference: https://www.openstreetmap.org/node/1402598729#map=17/51.98816/4.39126&layers=T
        _osm_id_node_to_validate = 4987298323
        # reference: https://www.openstreetmap.org/way/334316041#map=19/51.98945/4.39166&layers=T
        _osm_id_edge_to_validate = 334316041

        assert isinstance(graph_complex, Graph)
        assert _osm_id_node_to_validate in list(graph_complex.nodes.keys())
        assert _osm_id_edge_to_validate in list(map(lambda x: x["osmid"], graph_complex.edges.values()))

    @pytest.mark.parametrize("config", [
        pytest.param({
            "static": Path(__file__).parent / "test_data" / "graph" / "test_osm_network_wrapper" / "static",
            "network": {"polygon": None}
        }, id="None polygon file"),
        pytest.param({
            "static": Path(__file__).parent / "test_data" / "graph" / "test_osm_network_wrapper" / "static",
            "network": {"polygon": "invalid_name"}
        }, id="Invalid polygon file name")
    ])
    def test_download_graph_from_osm_with_invalid_polygon_parameter(self, config: dict):
        _osm_network = OsmNetworkWrapper(config=config)
        with pytest.raises(FileNotFoundError) as exc_err:
            _osm_network.download_graph_from_osm()

        assert str(exc_err.value) == "No or invalid polygon file is introduced for OSM download" or \
               "No polygon_file file found"