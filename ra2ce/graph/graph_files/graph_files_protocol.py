from pathlib import Path
from typing import Protocol, runtime_checkable

from geopandas import GeoDataFrame
from networkx import MultiGraph


@runtime_checkable
class GraphFileProtocol(Protocol):
    default_filename: Path
    file: Path
    graph: MultiGraph | GeoDataFrame

    def read_graph(self, file: Path) -> None:
        """
        Read a graph file

        Args:
            file (Path): Path to the file

        Returns: None
        """
        pass

    def get_graph(self) -> MultiGraph | GeoDataFrame:
        """
        Gets a graph file that is already known in the object.
        It is read if not done yet.

        Args: None

        Returns:
            MultiGraph | GeoDataFrame: the graph
        """
        pass
