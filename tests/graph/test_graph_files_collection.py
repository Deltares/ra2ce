from pathlib import Path

from ra2ce.graph.graph_files_collection import GraphFileProtocol, GraphFilesCollection
from tests import test_data


class TestGraphFilesCollection:
    def test_initialize(self):
        # 1. Define test data

        # 2. Execute test
        _collection = GraphFilesCollection()

        # 3. Verify results
        assert isinstance(_collection.base_graph, GraphFileProtocol)
        assert _collection.base_graph.file == None

    def test_get_filenames(self):
        # 1. Define test data

        # 2. Execute test
        _filenames = GraphFilesCollection().get_default_filenames()

        # 3. Verify results
        assert len(_filenames) == 6

    def test_set_files(self):
        # 1. Define test data
        _files = {
            "base_graph": Path("a"),
            "base_graph_hazard": Path("b"),
            "origins_destinations_graph": Path("c"),
            "origins_destinations_graph_hazard": Path("d"),
            "base_network": Path("e"),
            "base_network_hazard": Path("f"),
        }

        # 2. Execute test
        _collection = GraphFilesCollection.set_files(_files)

        # 3. Verify results
        assert _collection.base_graph.file == Path("a")
        assert _collection.base_graph_hazard.file == Path("b")
        assert _collection.origins_destinations_graph.file == Path("c")
        assert _collection.origins_destinations_graph_hazard.file == Path("d")
        assert _collection.base_network.file == Path("e")
        assert _collection.base_network_hazard.file == Path("f")

    def test_read_graph(self):
        # 1. Define test data
        _file = test_data.joinpath("readers_test_data", "base_graph.p")
        _collection = GraphFilesCollection()

        # 2. Execute test
        _collection.read_graph(_file)

        # 3. Verify results
        assert _collection.base_graph.file == _file
        assert _collection.base_graph.graph