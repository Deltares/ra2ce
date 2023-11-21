from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from geopandas import GeoDataFrame
from networkx import MultiGraph

from ra2ce.graph.graph_files.graph_file import GraphFile
from ra2ce.graph.graph_files.graph_files_enum import GraphFilesEnum
from ra2ce.graph.graph_files.graph_files_protocol import GraphFileProtocol
from ra2ce.graph.graph_files.network_file import NetworkFile


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

    def get_graph_file(self, type: GraphFilesEnum) -> GraphFileProtocol:
        """
        Get the graph (object)

        Args:
            type (GraphFileEnum): Type of graph file

        Raises:
            ValueError: If the type is not one of the known types

        Returns:
            GraphFileProtocol: Graph object of that specific type
        """
        if type == GraphFilesEnum.BASE_GRAPH:
            return self.base_graph
        elif type == GraphFilesEnum.BASE_GRAPH_HAZARD:
            return self.base_graph_hazard
        elif type == GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH:
            return self.origins_destinations_graph
        elif type == GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH_HAZARD:
            return self.origins_destinations_graph_hazard
        elif type == GraphFilesEnum.BASE_NETWORK:
            return self.base_network
        elif type == GraphFilesEnum.BASE_NETWORK_HAZARD:
            return self.base_network_hazard
        else:
            raise ValueError(f"Unknown graph type {type} provided.")

    def get_graph(self, type: GraphFilesEnum) -> GraphFileProtocol:
        """
        Get the graph

        Args:
            type (GraphFilesEnum): Type of graph file

        Returns:
            GraphFileProtocol: Graph of that specific type
        """
        _graph_file = self.get_graph_file(type)
        return _graph_file.graph

    def get_file(self, type: GraphFilesEnum) -> Path:
        """
        Get the file path to the graph

        Args:
            type (GraphFilesEnum): Type of graph file

        Returns:
            Path: Path to the graph file
        """
        _graph_file = self.get_graph_file(type)
        return _graph_file.file

    @classmethod
    def set_files(cls, files: dict[GraphFilesEnum, Path]) -> GraphFilesCollection:
        """
        Create a new collection with 1 or more graph files

        Args:
            files (dict[GraphFilesEnum, Path]): Dict containing the types and paths to the files

        Returns:
            GraphFilesCollection: Collection of graph files
        """
        _collection = cls()
        for _type, _path in files.items():
            _collection.set_file(_type, _path)
        return _collection

    def set_file(self, type: GraphFilesEnum, file: Path) -> None:
        """
        Set a path to a graph via the collection based on type of graph

        Args:
            type (GraphFilesEnum): Type of graph file
            file (Path): Path of the graph

        Raises:
            ValueError: If the type is not one of the known types
        """
        if type == GraphFilesEnum.BASE_GRAPH:
            self.base_graph.file = file
        elif type == GraphFilesEnum.BASE_GRAPH_HAZARD:
            self.base_graph_hazard.file = file
        elif type == GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH:
            self.origins_destinations_graph.file = file
        elif type == GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH_HAZARD:
            self.origins_destinations_graph_hazard.file = file
        elif type == GraphFilesEnum.BASE_NETWORK:
            self.base_network.file = file
        elif type == GraphFilesEnum.BASE_NETWORK_HAZARD:
            self.base_network_hazard.file = file
        else:
            raise ValueError(f"Unknown graph file type {type} provided.")

    def read_graph_file(self, file: Path) -> None:
        """
        Read a graph file via the collection

        Args:
            file (Path): Path fo the graph

        Raises:
            ValueError: If the type is not one of the known types

        Returns: None
        """
        if file.name == self.base_graph.default_filename.name:
            self.base_graph.read_graph_file(file)
        elif file.name == self.base_graph_hazard.default_filename.name:
            self.base_graph_hazard.read_graph_file(file)
        elif file.name == self.origins_destinations_graph.default_filename.name:
            self.origins_destinations_graph.read_graph_file(file)
        elif file.name == self.origins_destinations_graph_hazard.default_filename.name:
            self.origins_destinations_graph_hazard.read_graph_file(file)
        elif file.name == self.base_network.default_filename.name:
            self.base_network.read_graph_file(file)
        elif file.name == self.base_network_hazard.default_filename.name:
            self.base_network_hazard.read_graph_file(file)
        else:
            raise ValueError(f"Unknown graph file {file} provided.")
