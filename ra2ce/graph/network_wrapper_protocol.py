from typing import Protocol, runtime_checkable
from geopandas import GeoDataFrame
from networkx import MultiGraph


@runtime_checkable
class NetworkWrapperProtocol(Protocol):
    def get_network(self) -> tuple[MultiGraph, GeoDataFrame]:
        """
        Gets a network built within this wrapper instance. No arguments are accepted, the `__init__` method is meant to assign all required attributes for a wrapper.

        Returns:
            tuple[MultiGraph, GeoDataFrame]: Tuple of MultiGraph representing the graph and GeoDataFrame representing the network.
        """
        pass
