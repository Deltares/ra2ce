from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from geopandas import GeoDataFrame, read_feather
from networkx import MultiGraph

from ra2ce.common.io.readers.graph_pickle_reader import GraphPickleReader


class GraphFileEnum(Enum):
    BASE_GRAPH = 1
    BASE_GRAPH_HAZARD = 2
    ORIGINS_DESTINATIONS_GRAPH = 3
    ORIGINS_DESTINATIONS_GRAPH_HAZARD = 4
    BASE_NETWORK = 5
    BASE_NETWORK_HAZARD = 6


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


@dataclass
class GraphFile(GraphFileProtocol):
    default_filename: Path = None
    file: Path = None
    graph: MultiGraph = None

    def read_graph_file(self, file: Path) -> MultiGraph:
        self.file = file
        self.read_graph()
        return self.graph

    def read_graph(self) -> MultiGraph:
        if self.file.is_file():
            _pickle_reader = GraphPickleReader()
            self.graph = _pickle_reader.read(self.file)
        return self.graph


@dataclass
class NetworkFile(GraphFileProtocol):
    default_filename: Path = None
    file: Path = None
    graph: GeoDataFrame = None

    def read_graph_file(self, file: Path) -> MultiGraph:
        self.file = file
        self.read_graph()
        return self.graph

    def read_graph(self) -> MultiGraph:
        if self.file.is_file():
            self.graph = read_feather(self.file)
        return self.graph


@dataclass
class GraphFilesCollection:
    base_graph: GraphFile = field(
        default_factory=lambda: GraphFile(default_filename=Path("base_graph.p"))
    )
    base_graph_hazard: GraphFile = field(
        default_factory=lambda: GraphFile(default_filename=Path("base_graph_hazard.p"))
    )
    origins_destinations_graph: GraphFile = field(
        default_factory=lambda: GraphFile(
            default_filename=Path("origins_destinations_graph.p")
        )
    )
    origins_destinations_graph_hazard: GraphFile = field(
        default_factory=lambda: GraphFile(
            default_filename=Path("origins_destinations_graph_hazard.p")
        )
    )
    base_network: NetworkFile = field(
        default_factory=lambda: NetworkFile(
            default_filename=Path("base_network.feather")
        )
    )
    base_network_hazard: NetworkFile = field(
        default_factory=lambda: NetworkFile(
            default_filename=Path("base_network_hazard.feather")
        )
    )

    def has_graphs(self) -> bool:
        """
        Tests if any of the types has a graph already read

        Returns:
            bool: True if any graph already read
        """
        return (
            self.base_graph.graph
            or self.base_graph_hazard.graph
            or self.origins_destinations_graph.graph
            or self.origins_destinations_graph_hazard
            or self.base_network.graph
            or self.base_network_hazard.graph
        )

    def get_default_filenames(self) -> list[str]:
        """
        Get the default file names for all types

        Returns:
            list[str]: List of all default filenames
        """
        return [
            self.base_graph.default_filename.name,
            self.base_graph_hazard.default_filename.name,
            self.origins_destinations_graph.default_filename.name,
            self.origins_destinations_graph_hazard.default_filename.name,
            self.base_network.default_filename.name,
            self.base_network_hazard.default_filename.name,
        ]

    def get_graph_file(self, type: str) -> GraphFileProtocol:
        """
        Get the graph (object)

        Args:
            type (str): Type of graph

        Raises:
            ValueError: If the type is not one of the known types

        Returns:
            GraphFileProtocol: Graph object of that specific type
        """
        if type.upper() == GraphFileEnum.BASE_GRAPH.name:
            return self.base_graph
        elif type.upper() == GraphFileEnum.BASE_GRAPH_HAZARD.name:
            return self.base_graph_hazard
        elif type.upper() == GraphFileEnum.ORIGINS_DESTINATIONS_GRAPH.name:
            return self.origins_destinations_graph
        elif type.upper() == GraphFileEnum.ORIGINS_DESTINATIONS_GRAPH_HAZARD.name:
            return self.origins_destinations_graph_hazard
        elif type.upper() == GraphFileEnum.BASE_NETWORK.name:
            return self.base_network
        elif type.upper() == GraphFileEnum.BASE_NETWORK_HAZARD.name:
            return self.base_network_hazard
        else:
            raise ValueError(f"Unknown graph type {type} provided.")

    def get_graph(self, type: str) -> GraphFileProtocol:
        """
        Get the graph

        Args:
            type (str): Type of graph

        Returns:
            GraphFileProtocol: Graph of that specific type
        """
        _graph_file = self.get_graph_file(type)
        return _graph_file.graph

    def get_file(self, type: str) -> Path:
        """
        Get the file path to the graph

        Args:
            type (str): Type of graph

        Returns:
            Path: Path to the graph file
        """
        _graph_file = self.get_graph_file(type)
        return _graph_file.file

    @classmethod
    def set_files(cls, files: dict[str, Path]) -> GraphFilesCollection:
        """
        Create a new collection with 1 or more graph files

        Args:
            files (dict[str, Path]): Dict containing the types and paths to the files

        Returns:
            GraphFilesCollection: Collection of graph files
        """
        _collection = cls()
        for _type, _path in files.items():
            _collection.set_file(_type, _path)
        return _collection

    def set_file(self, type: str, file: Path) -> None:
        """
        Set a path to a graph via the collection based on type of graph

        Args:
            type (str): Type of graph
            file (Path): Path of the graph

        Raises:
            ValueError: If the type is not one of the known types
        """
        if type.upper() == GraphFileEnum.BASE_GRAPH.name:
            self.base_graph.file = file
        elif type.upper() == GraphFileEnum.BASE_GRAPH_HAZARD.name:
            self.base_graph_hazard.file = file
        elif type.upper() == GraphFileEnum.ORIGINS_DESTINATIONS_GRAPH.name:
            self.origins_destinations_graph.file = file
        elif type.upper() == GraphFileEnum.ORIGINS_DESTINATIONS_GRAPH_HAZARD.name:
            self.origins_destinations_graph_hazard.file = file
        elif type.upper() == GraphFileEnum.BASE_NETWORK.name:
            self.base_network.file = file
        elif type.upper() == GraphFileEnum.BASE_NETWORK_HAZARD.name:
            self.base_network_hazard.file = file
        else:
            raise ValueError(f"Unknown graph file type {type} provided.")

    def read_graph_file(self, file: Path) -> MultiGraph | GeoDataFrame:
        """
        Read a graph file via the collection

        Args:
            file (Path): Path fo the graph

        Raises:
            ValueError: If the type is not one of the known types

        Returns:
            MultiGraph | GeoDataFrame: The graph
        """
        if file.name == self.base_graph.default_filename.name:
            _graph = self.base_graph.read_graph_file(file)
        elif file.name == self.base_graph_hazard.default_filename.name:
            _graph = self.base_graph_hazard.read_graph_file(file)
        elif file.name == self.origins_destinations_graph.default_filename.name:
            _graph = self.origins_destinations_graph.read_graph_file(file)
        elif file.name == self.origins_destinations_graph_hazard.default_filename.name:
            _graph = self.origins_destinations_graph_hazard.read_graph_file(file)
        elif file.name == self.base_network.default_filename.name:
            _graph = self.base_network.read_graph_file(file)
        elif file.name == self.base_network_hazard.default_filename.name:
            _graph = self.base_network_hazard.read_graph_file(file)
        else:
            raise ValueError(f"Unknown graph file {file} provided.")
        return _graph
