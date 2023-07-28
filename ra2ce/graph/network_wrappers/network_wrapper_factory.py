from geopandas import GeoDataFrame
from networkx import MultiGraph
from ra2ce.graph.network_config_data.network_config_data import NetworkConfigData
from ra2ce.graph.network_wrappers.network_wrapper_protocol import NetworkWrapperProtocol
from ra2ce.graph.network_wrappers.shp_network_wrapper import ShpNetworkWrapper
from ra2ce.graph.network_wrappers.vector_network_wrapper import VectorNetworkWrapper
import logging
from ra2ce.graph.network_wrappers.osm_network_wrapper.osm_network_wrapper import (
    OsmNetworkWrapper,
)
from ra2ce.graph.network_wrappers.trails_network_wrapper import (
    TrailsNetworkWrapper,
)
from ra2ce.common.io.readers import GraphPickleReader
import geopandas as gpd


class NetworkWrapperFactory(NetworkWrapperProtocol):
    def __init__(self, config_data: NetworkConfigData) -> None:
        self._config_data = config_data

    def _any_cleanup_enabled(self) -> bool:
        _cleanup = self._config_data.cleanup
        return (
            _cleanup.snapping_threshold
            or _cleanup.pruning_threshold
            or _cleanup.merge_lines
            or _cleanup.cut_at_intersections
        )

    def get_network(self) -> tuple[MultiGraph, GeoDataFrame]:
        logging.info("Start creating a network from the submitted shapefile.")
        source = self._config_data.network.source
        if source == "shapefile":
            if self._any_cleanup_enabled():
                return ShpNetworkWrapper(self._config_data).get_network()
            return VectorNetworkWrapper(self._config_data).get_network()
        elif source == "OSM PBF":
            return TrailsNetworkWrapper(self._config_data).get_network()
        elif source == "OSM download":
            return OsmNetworkWrapper(self._config_data).get_network()
        elif source == "pickle":
            logging.info("Start importing a network from pickle")
            base_graph = GraphPickleReader().read(
                self.output_graph_dir.joinpath("base_graph.p")
            )
            network_gdf = gpd.read_feather(
                self.output_graph_dir.joinpath("base_network.feather")
            )
            return base_graph, network_gdf
