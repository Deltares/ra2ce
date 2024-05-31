from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.network.graph_files.graph_files_protocol import GraphFileProtocol
from ra2ce.network.graph_files.network_file import NetworkFile


class TestNetworkFile:
    def test_initialize(self):
        # 1-2. Execute test
        _nf = NetworkFile()

        # 3. Verify results
        assert isinstance(_nf, GraphFileProtocol)

    def test_get_file_without_graph_is_none(self):
        # 1-2. Execute test
        _nf = NetworkFile(name="base_network.feather")

        # 3. Verify results
        assert _nf.file is None

    def test_read_graph(self, graph_folder: Path):
        # 1. Define test data
        _name = "base_network.feather"
        _file = graph_folder.joinpath(_name)
        _nf = NetworkFile(name=_name)

        # 2. Execute test
        _nf.read_graph(graph_folder)

        # 3. Verify results
        assert _nf.file == _file
        assert _nf.graph is not None

    def test_get_graph_without_graph_is_none(self):
        # 1. Define test data
        _nf = NetworkFile()

        # 2. Execute test
        _graph = _nf.get_graph()

        # 3. Verify results
        assert _graph is None

    def test_get_graph(self, graph_folder: Path):
        # 1. Define test data
        _name = "base_network.feather"
        _nf = NetworkFile(name=_name)
        _nf.read_graph(graph_folder)

        # 2. Execute test
        _graph = _nf.get_graph()

        # 3. Verify results
        assert _graph is not None
        assert len(_graph) == len(_nf.graph)
        assert isinstance(_graph, GeoDataFrame)
