from dataclasses import dataclass
from pathlib import Path

from networkx import MultiGraph

from ra2ce.common.io.readers.graph_pickle_reader import GraphPickleReader
from ra2ce.graph.graph_files.graph_files_protocol import GraphFileProtocol


@dataclass
class GraphFile(GraphFileProtocol):
    """
    Not this class resembles NetworkFile to a large extent
    """

    name: str = ""
    folder: Path = None
    graph: MultiGraph = None

    @property
    def file(self) -> Path | None:
        if not self.folder:
            return None
        return self.folder.joinpath(self.name)

    def read_graph(self, folder: Path) -> None:
        self.folder = folder
        if self.file and self.file.is_file():
            _pickle_reader = GraphPickleReader()
            self.graph = _pickle_reader.read(self.file)

    def get_graph(self) -> MultiGraph:
        if self.graph is None:
            self.read_graph(self.folder)
        return self.graph
