from pathlib import Path

from ra2ce.graph.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.graph.graph_files.graph_files_enum import GraphFilesEnum
from ra2ce.graph.graph_files.graph_files_protocol import GraphFileProtocol
from tests import test_data


class TestGraphFilesCollection:
    def test_initialize(self):
        # 1. Define test data

        # 2. Execute test
        _collection = GraphFilesCollection()

        # 3. Verify results
        assert isinstance(_collection.base_graph, GraphFileProtocol)
        assert _collection.base_graph.file == None

    def test_set_file(self):
        # 1. Define test data
        _type = GraphFilesEnum.BASE_GRAPH
        _file = "dummy"
        _collection = GraphFilesCollection()

        # 2. Execute test
        _collection.set_file(_type, _file)

        # 3. Verify results
        assert _collection.get_file(_type) == _file

    def test_set_files(self):
        # 1. Define test data
        _dir = test_data.joinpath("readers_test_data")
        _file = _dir.joinpath("base_graph.p")
        _collection = GraphFilesCollection()

        # 2. Execute test
        _collection.set_files(_dir)

        # 3. Verify results
        _collection.base_graph.file = _file

    def test_read_graph_on_graph(self):
        # 1. Define test data
        _file = test_data.joinpath("readers_test_data", "base_graph.p")
        _collection = GraphFilesCollection()

        # 2. Execute test
        _collection.base_graph.read_graph(_file)

        # 3. Verify results
        assert _collection.base_graph.file == _file
        assert _collection.base_graph.graph

    def test_get_graph_on_graph(self):
        # 1. Define test data
        _file = test_data.joinpath("readers_test_data", "base_graph.p")
        _collection = GraphFilesCollection()
        _collection.base_graph.read_graph(_file)

        # 2. Execute test
        _graph = _collection.base_graph.get_graph()

        # 3. Verify results
        assert _collection.base_graph.file == _file
        assert _collection.base_graph.graph == _graph
        assert _graph

    def test_has_graphs_without_graphs(self):
        # 1. Define test data
        _collection = GraphFilesCollection()

        # 2. Execute test
        _result = _collection.has_graphs()

        # 3. Verify results
        assert not _result

    def test_has_graphs_with_graphs(self):
        # 1. Define test data
        _file = test_data.joinpath("readers_test_data", "base_graph.p")
        _collection = GraphFilesCollection()
        _collection.base_graph.read_graph(_file)

        # 2. Execute test
        _result = _collection.has_graphs()

        # 3. Verify results
        assert _result
