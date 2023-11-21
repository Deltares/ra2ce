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

    def read_graph(self, file: Path) -> None:
        self.file = file
        if self.file.is_file():
            self.graph = read_feather(self.file)

    def get_graph(self) -> GeoDataFrame:
        if not self.graph:
            self.read_graph(self.file)
        return self.graph
