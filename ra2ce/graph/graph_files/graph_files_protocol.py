from pathlib import Path
from typing import Protocol, runtime_checkable

from geopandas import GeoDataFrame
from networkx import MultiGraph


@runtime_checkable
class GraphFileProtocol(Protocol):
    default_filename: Path
    file: Path
    graph: MultiGraph | GeoDataFrame

    def read_graph_file(self, file: Path) -> MultiGraph | GeoDataFrame:
        """
        Read a graph file

        Args:
            file (Path): Path to the file

        Returns:
            MultiGraph | GeoDataFrame: the graph
        """
        pass

    def read_graph(self) -> MultiGraph | GeoDataFrame:
        """
        Read a graph file that is already known in the object

        Args: None

        Returns:
            MultiGraph | GeoDataFrame: the graph
        """
        pass
