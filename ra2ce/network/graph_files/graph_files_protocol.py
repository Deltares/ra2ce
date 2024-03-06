from pathlib import Path
from typing import Protocol, runtime_checkable

from geopandas import GeoDataFrame
from networkx import MultiGraph


@runtime_checkable
class GraphFileProtocol(Protocol):
    name: str
    folder: Path
    graph: MultiGraph | GeoDataFrame

    @property
    def file(self) -> Path | None:
        """
        Return the path to the graph

        Returns:
            Path | None: _description_
        """

    def read_graph(self, folder: Path) -> None:
        """
        Read a graph file

        Args:
            folder (Path): Folder of the graph

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
