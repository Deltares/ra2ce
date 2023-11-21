from dataclasses import dataclass
from pathlib import Path

from networkx import MultiGraph

from ra2ce.common.io.readers.graph_pickle_reader import GraphPickleReader
from ra2ce.graph.graph_files.graph_files_protocol import GraphFileProtocol


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
