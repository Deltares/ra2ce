from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from geopandas import GeoDataFrame
from networkx import MultiGraph

from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.graph_files.graph_files_protocol import GraphFileProtocol
from ra2ce.network.graph_files.network_file import NetworkFile


@dataclass
class GraphFilesCollection:
    """
    Class containing a collection of the graphs and the paths to the files.
    The names of the graph file are assumed to be standardized (e.g. "base_graph.p").
    """

    base_graph: GraphFile = field(
        default_factory=lambda: GraphFile(name="base_graph.p")
    )
    base_graph_hazard: GraphFile = field(
        default_factory=lambda: GraphFile(name="base_graph_hazard.p")
    )
    origins_destinations_graph: GraphFile = field(
        default_factory=lambda: GraphFile(name="origins_destinations_graph.p")
    )
    origins_destinations_graph_hazard: GraphFile = field(
        default_factory=lambda: GraphFile(name="origins_destinations_graph_hazard.p")
    )
    base_network: NetworkFile = field(
        default_factory=lambda: NetworkFile(name="base_network.feather")
    )
    base_network_hazard: NetworkFile = field(
        default_factory=lambda: NetworkFile(name="base_network_hazard.feather")
    )
    locations_hazard: NetworkFile = field(
        default_factory=lambda: NetworkFile(name="locations_hazard.feather")
    )

    @property
    def _graph_collection(self) -> list[GraphFile | NetworkFile]:
        return [
            self.base_graph,
            self.base_graph_hazard,
            self.origins_destinations_graph,
            self.origins_destinations_graph_hazard,
            self.base_network,
            self.base_network_hazard,
            self.locations_hazard,
        ]

    def has_graphs(self) -> bool:
        """
        Tests if any of the types has a graph already read

        Returns:
            bool: True if any graph already read
        """

        def has_graph(gf: GraphFileProtocol) -> bool:
            return gf.graph is not None

        return any(filter(has_graph, self._graph_collection))

    def _get_graph_file(self, graph_file_type: str) -> GraphFileProtocol:
        """
        Get the graph (object)

        Args:
            graph_file_type (str): Type of graph file

        Raises:
            ValueError: If the graph_file_type is not one of the known types

        Returns:
            GraphFileProtocol: Graph object of that specific graph_file_type
        """
        _gf = next(
            (
                gf
                for gf in self._graph_collection
                if Path(gf.name).stem == graph_file_type
            ),
            None,
        )
        if _gf is None:
            raise ValueError(f"Unknown graph file type {graph_file_type} provided.")
        return _gf

    def get_graph(self, graph_file_type: str) -> MultiGraph | GeoDataFrame:
        """
        Get the graph

        Args:
            graph_file_type (str): Type of graph file

        Returns:
            GraphFileProtocol: Graph of that specific graph_file_type
        """
        _gf = self._get_graph_file(graph_file_type)
        return _gf.get_graph()

    def get_file(self, graph_file_type: str) -> Path | None:
        """
        Get the file path to the graph

        Args:
            graph_file_type (str): Type of graph file

        Returns:
            Path: Path to the graph file
        """
        _gf = self._get_graph_file(graph_file_type)
        return _gf.file

    @classmethod
    def set_files(cls, parent_dir: Path) -> GraphFilesCollection:
        """
        Create a new collection with 1 or more graph files that match the default names

        Args:
            parent_dir (Path): Path of the parent folder in which the files are searched

        Returns:
            GraphFilesCollection: Collection of graphs
        """
        _collection = cls()

        _collection.base_graph.read_graph(parent_dir)
        _collection.base_graph_hazard.read_graph(parent_dir)
        _collection.origins_destinations_graph.read_graph(parent_dir)
        _collection.origins_destinations_graph_hazard.read_graph(parent_dir)
        _collection.base_network.read_graph(parent_dir)
        _collection.base_network_hazard.read_graph(parent_dir)
        _collection.locations_hazard.read_graph(parent_dir)

        return _collection

    def set_file(self, file: Path) -> None:
        """
        Set a path to a graph via the collection

        Args:
            file (Path): Path of the graph

        Raises:
            ValueError: If the graph_file_type is not one of the known types
        """
        _gf = self._get_graph_file(file.stem)
        _gf.folder = file.parent

    def set_graph(self, graph_file_type: str, graph: MultiGraph | GeoDataFrame):
        """
        Set a graph via the collection based on type of graph

        Args:
            graph_file_type (str): Type of graph file
            graph (MultiGraph | GeoDataFrame): The graph

        Raises:
            ValueError: If the graph_file_type is not one of the known types
        """
        _gf = self._get_graph_file(graph_file_type)
        _gf.graph = graph

    def read_graph(self, file: Path) -> None:
        """
        Read a graph file via the collection

        Args:
            file (Path): Path fo the graph

        Raises:
            ValueError: If the graph_file_type is not one of the known types

        Returns: None
        """
        _gf = next((gf for gf in self._graph_collection if gf.name == file.name), None)
        if _gf is None:
            raise ValueError(f"Unknown graph file {file} provided.")
        _gf.read_graph(file.parent)
