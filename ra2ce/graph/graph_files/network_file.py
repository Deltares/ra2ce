from dataclasses import dataclass
from pathlib import Path

from geopandas import GeoDataFrame
from pandas import read_feather

from ra2ce.graph.graph_files.graph_files_protocol import GraphFileProtocol


@dataclass
class NetworkFile(GraphFileProtocol):
    default_filename: Path = None
    file: Path = None
    graph: GeoDataFrame = None

    def read_graph_file(self, file: Path) -> GeoDataFrame:
        self.file = file
        self.read_graph()
        return self.graph

    def read_graph(self) -> GeoDataFrame:
        if self.file.is_file():
            self.graph = read_feather(self.file)
        return self.graph
