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

    def test_get_default_filenames(self):
        # 1. Define test data

        # 2. Execute test
        _filenames = GraphFilesCollection().get_default_filenames()

        # 3. Verify results
        assert len(_filenames) == 6

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
        _files = {
            GraphFilesEnum.BASE_GRAPH: Path("a"),
            GraphFilesEnum.BASE_GRAPH_HAZARD: Path("b"),
            GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH: Path("c"),
            GraphFilesEnum.ORIGINS_DESTINATIONS_GRAPH_HAZARD: Path("d"),
            GraphFilesEnum.BASE_NETWORK: Path("e"),
            GraphFilesEnum.BASE_NETWORK_HAZARD: Path("f"),
        }

        # 2. Execute test
        _collection = GraphFilesCollection().set_files(_files)

        # 3. Verify results
        assert _collection.base_graph.file == Path("a")
        assert _collection.base_graph_hazard.file == Path("b")
        assert _collection.origins_destinations_graph.file == Path("c")
        assert _collection.origins_destinations_graph_hazard.file == Path("d")
        assert _collection.base_network.file == Path("e")
        assert _collection.base_network_hazard.file == Path("f")

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
