from networkx import MultiGraph

from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.graph_files.graph_files_protocol import GraphFileProtocol
from tests import test_data

_GRAPH_FOLDER = test_data.joinpath(r"simple_inputs\static\output_graph")


class TestGraphFile:
    def test_initialize(self):
        # 1. Define test data

        # 2. Execute test
        _gf = GraphFile()

        # 3. Verify results
        assert isinstance(_gf, GraphFileProtocol)

    def test_get_file_without_graph_is_none(self):
        # 1. Define test data

        # 2. Execute test
        _gf = GraphFile(name="base_graph.p")

        # 3. Verify results
        assert _gf.file is None

    def test_read_graph(self):
        # 1. Define test data
        _name = "base_graph.p"
        _file = _GRAPH_FOLDER.joinpath(_name)
        _gf = GraphFile(name=_name)

        # 2. Execute test
        _gf.read_graph(_GRAPH_FOLDER)

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

    def test_get_graph(self):
        # 1. Define test data
        _name = "base_graph.p"
        _gf = GraphFile(name=_name)
        _gf.read_graph(_GRAPH_FOLDER)

        # 2. Execute test
        _graph = _gf.get_graph()

        # 3. Verify results
        assert _graph is not None
        assert _graph == _gf.graph
        assert isinstance(_graph, MultiGraph)
