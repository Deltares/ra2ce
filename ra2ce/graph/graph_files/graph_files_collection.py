from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

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

    @property
    def _graph_collection(self) -> list[GraphFile | NetworkFile]:
        return [
            self.base_graph,
            self.base_graph_hazard,
            self.origins_destinations_graph,
            self.origins_destinations_graph_hazard,
            self.base_network,
            self.base_network_hazard,
        ]

    def has_graphs(self) -> bool:
        """
        Tests if any of the types has a graph already read

        Returns:
            bool: True if any graph already read
        """
        return next(
            iter([x for x in self._graph_collection if x.graph is not None]),
            False,
        )

    def get_graph_file(self, graph_file_type: GraphFilesEnum) -> GraphFileProtocol:
        """
        Get the graph (object)

        Args:
            graph_file_type (GraphFileEnum): Type of graph file

        Raises:
            ValueError: If the graph_file_type is not one of the known types

        Returns:
            GraphFileProtocol: Graph object of that specific graph_file_type
        """
        if graph_file_type == GraphFilesEnum.BASE_GRAPH:
            return self.base_graph
        elif graph_file_type == GraphFilesEnum.BASE_GRAPH_HAZARD:
            return self.base_graph_hazard
        elif graph_file_type == GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH:
            return self.origins_destinations_graph
        elif graph_file_type == GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH_HAZARD:
            return self.origins_destinations_graph_hazard
        elif graph_file_type == GraphFilesEnum.BASE_NETWORK:
            return self.base_network
        elif graph_file_type == GraphFilesEnum.BASE_NETWORK_HAZARD:
            return self.base_network_hazard
        else:
            raise ValueError(f"Unknown graph file type {graph_file_type} provided.")

    def get_graph(self, graph_file_type: GraphFilesEnum) -> GraphFileProtocol:
        """
        Get the graph

        Args:
            graph_file_type (GraphFilesEnum): Type of graph file

        Returns:
            GraphFileProtocol: Graph of that specific graph_file_type
        """
        _graph_file = self.get_graph_file(graph_file_type)
        return _graph_file.graph

    def get_file(self, graph_file_type: GraphFilesEnum) -> Path:
        """
        Get the file path to the graph

        Args:
            graph_file_type (GraphFilesEnum): Type of graph file

        Returns:
            Path: Path to the graph file
        """
        _graph_file = self.get_graph_file(graph_file_type)
        return _graph_file.file

    def set_files(self, parent_dir: Path):
        """
        Create a new collection with 1 or more graph files that match the default names

        Args:
            parent_dir (Path): Path of the parent folder in which the files are searched

        Returns: None
        """
        for _file in parent_dir.iterdir():
            _match = next(
                iter(
                    [
                        x
                        for x in self._graph_collection
                        if x.default_filename.name == _file.name
                    ]
                ),
                False,
            )
            if _match:
                self.set_file(
                    GraphFilesEnum[_match.default_filename.stem.upper()], _file
                )

    def set_file(self, graph_file_type: GraphFilesEnum, file: Path) -> None:
        """
        Set a path to a graph via the collection based on type of graph

        Args:
            graph_file_type (GraphFilesEnum): Type of graph file
            file (Path): Path of the graph

        Raises:
            ValueError: If the graph_file_type is not one of the known types
        """
        if graph_file_type == GraphFilesEnum.BASE_GRAPH:
            self.base_graph.file = file
        elif graph_file_type == GraphFilesEnum.BASE_GRAPH_HAZARD:
            self.base_graph_hazard.file = file
        elif graph_file_type == GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH:
            self.origins_destinations_graph.file = file
        elif graph_file_type == GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH_HAZARD:
            self.origins_destinations_graph_hazard.file = file
        elif graph_file_type == GraphFilesEnum.BASE_NETWORK:
            self.base_network.file = file
        elif graph_file_type == GraphFilesEnum.BASE_NETWORK_HAZARD:
            self.base_network_hazard.file = file
        else:
            raise ValueError(f"Unknown graph file type {graph_file_type} provided.")

    def read_graph(self, file: Path) -> None:
        """
        Read a graph file via the collection

        Args:
            file (Path): Path fo the graph

        Raises:
            ValueError: If the graph_file_type is not one of the known types

        Returns: None
        """
        if file.name == self.base_graph.default_filename.name:
            self.base_graph.read_graph(file)
        elif file.name == self.base_graph_hazard.default_filename.name:
            self.base_graph_hazard.read_graph(file)
        elif file.name == self.origins_destinations_graph.default_filename.name:
            self.origins_destinations_graph.read_graph(file)
        elif file.name == self.origins_destinations_graph_hazard.default_filename.name:
            self.origins_destinations_graph_hazard.read_graph(file)
        elif file.name == self.base_network.default_filename.name:
            self.base_network.read_graph(file)
        elif file.name == self.base_network_hazard.default_filename.name:
            self.base_network_hazard.read_graph(file)
        else:
            raise ValueError(f"Unknown graph file {file} provided.")
