from typing import Protocol, runtime_checkable
from geopandas import GeoDataFrame
from networkx import MultiGraph


@runtime_checkable
class NetworkWrapperProtocol(Protocol):
    def get_network(self, **kwargs) -> tuple[MultiGraph, GeoDataFrame]:
        """
        Gets a network built within this wrapper instance.

        Returns:
            tuple[MultiGraph, GeoDataFrame]: Tuple of MultiGraph representing the graph and GeoDataFrame representing the network.
        """
        pass
