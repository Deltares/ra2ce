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
    graph: GeoDataFrame | Any

    def read_graph(self, file: Path) -> None:
        """
        Read a graph file

        Args:
            file (Path): Path to the file
        """
        pass


@dataclass
class GraphFile(GraphFileProtocol):
    default_filename: Path = None
    file: Path = None
    graph: MultiGraph = None

    def read_graph(self, file: Path | None) -> None:
        if file:
            self.file = file
        if self.file.is_file():
            _pickle_reader = GraphPickleReader()
            self.graph = _pickle_reader.read(self.file)
        else:
            pass


@dataclass
class NetworkFile(GraphFileProtocol):
    default_filename: Path = None
    file: Path = None
    graph: GeoDataFrame = None

    def read_graph(self, file: Path | None) -> None:
        if file:
            self.file = file
        if self.file.is_file():
            self.graph = read_feather(self.file)
        else:
            pass


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

    def has_graphs(self):
        return (
            self.base_graph.graph
            or self.base_graph_hazard.graph
            or self.origins_destinations_graph.graph
            or self.origins_destinations_graph_hazard
            or self.base_network.graph
            or self.base_network_hazard.graph
        )

    def get_default_filenames(self) -> list[str]:
        return [
            self.base_graph.default_filename.name,
            self.base_graph_hazard.default_filename.name,
            self.origins_destinations_graph.default_filename.name,
            self.origins_destinations_graph_hazard.default_filename.name,
            self.base_network.default_filename.name,
            self.base_network_hazard.default_filename.name,
        ]

    def get_graph_file(self, type: str) -> GraphFileProtocol:
        if type == self.base_graph.default_filename.stem:
            return self.base_graph
        elif type == self.base_graph_hazard.default_filename.stem:
            return self.base_graph_hazard
        elif type == self.origins_destinations_graph.default_filename.stem:
            return self.origins_destinations_graph
        elif type == self.origins_destinations_graph_hazard.default_filename.stem:
            return self.origins_destinations_graph_hazard
        elif type == self.base_network.default_filename.stem:
            return self.base_network
        elif type == self.base_network_hazard.default_filename.stem:
            return self.base_network_hazard
        else:
            raise ValueError(f"Unknown graph type {type} provided.")

    def get_graph(self, type: str) -> GraphFileProtocol:
        _graph_file = self.get_graph_file(type)
        return _graph_file.graph

    def get_file(self, type: str) -> Path:
        _graph_file = self.get_graph_file(type)
        return _graph_file.file

    @classmethod
    def set_files(cls, files: dict[str, Path]) -> GraphFilesCollection:
        _collection = cls()
        for _file, _path in files.items():
            if _file.upper() == GraphFileEnum.BASE_GRAPH.name:
                _collection.base_graph.file = _path
            elif _file.upper() == GraphFileEnum.BASE_GRAPH_HAZARD.name:
                _collection.base_graph_hazard.file = _path
            elif _file.upper() == GraphFileEnum.ORIGINS_DESTINATIONS_GRAPH.name:
                _collection.origins_destinations_graph.file = _path
            elif _file.upper() == GraphFileEnum.ORIGINS_DESTINATIONS_GRAPH_HAZARD.name:
                _collection.origins_destinations_graph_hazard.file = _path
            elif _file.upper() == GraphFileEnum.BASE_NETWORK.name:
                _collection.base_network.file = _path
            elif _file.upper() == GraphFileEnum.BASE_NETWORK_HAZARD.name:
                _collection.base_network_hazard.file = _path
            else:
                raise ValueError(f"Unknown graph file {_file} provided.")
        return _collection

    def read_graph(self, file: Path) -> None:
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
