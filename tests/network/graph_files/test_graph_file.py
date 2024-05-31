from pathlib import Path

from networkx import MultiGraph

from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.graph_files.graph_files_protocol import GraphFileProtocol


class TestGraphFile:
    def test_initialize(self):
        # 1-2. Execute test
        _gf = GraphFile()

        # 3. Verify results
        assert isinstance(_gf, GraphFileProtocol)

    def test_get_file_without_graph_is_none(self):
        # 1-2. Execute test
        _gf = GraphFile(name="base_graph.p")

        # 3. Verify results
        assert _gf.file is None

    def test_read_graph(self, graph_folder: Path):
        # 1. Define test data
        _name = "base_graph.p"
        _file = graph_folder.joinpath(_name)
        _gf = GraphFile(name=_name)

        # 2. Execute test
        _gf.read_graph(graph_folder)

        # 3. Verify results
        assert _gf.file == _file
        assert _gf.graph is not None

    def test_get_graph_without_graph_is_none(self):
        # 1. Define test data
        _gf = GraphFile()

        # 2. Execute test
        _graph = _gf.get_graph()

        # 3. Verify results
        assert _graph is None

    def test_get_graph(self, graph_folder: Path):
        # 1. Define test data
        _name = "base_graph.p"
        _gf = GraphFile(name=_name)
        _gf.read_graph(graph_folder)

        # 2. Execute test
        _graph = _gf.get_graph()

        # 3. Verify results
        assert _graph is not None
        assert _graph == _gf.graph
        assert isinstance(_graph, MultiGraph)
