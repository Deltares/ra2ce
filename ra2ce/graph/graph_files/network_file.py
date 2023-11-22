from dataclasses import dataclass
from pathlib import Path

from geopandas import GeoDataFrame
from pandas import read_feather

from ra2ce.graph.graph_files.graph_files_protocol import GraphFileProtocol


@dataclass
class NetworkFile(GraphFileProtocol):
    name: str = ""
    folder: Path = None
    graph: GeoDataFrame = None

    @property
    def file(self) -> Path | None:
        if not self.folder:
            return None
        return self.folder.joinpath(self.name)

    def read_graph(self, folder: Path) -> None:
        self.folder = folder
        if self.file and self.file.is_file():
            self.graph = read_feather(self.file)

    def get_graph(self) -> GeoDataFrame:
        if not self.graph:
            self.read_graph(self.folder)
        return self.graph
