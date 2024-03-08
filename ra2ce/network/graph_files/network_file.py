from dataclasses import dataclass
from pathlib import Path

from geopandas import GeoDataFrame, read_feather

from ra2ce.network.graph_files.graph_files_protocol import GraphFileProtocol


@dataclass
class NetworkFile(GraphFileProtocol):
    """
    Note this class resembles GraphFile to a large extent
    """

    name: str = ""
    folder: Path = None
    graph: GeoDataFrame = None

    @property
    def file(self) -> Path | None:
        if not self.folder:
            return None
        return self.folder.joinpath(self.name)

    def read_graph(self, folder: Path) -> None:
        if not folder:
            return
        _file = folder.joinpath(self.name)
        if _file and _file.is_file():
            self.folder = folder
            self.graph = read_feather(self.file)

    def get_graph(self) -> GeoDataFrame:
        if self.graph is None:
            self.read_graph(self.folder)
        return self.graph
