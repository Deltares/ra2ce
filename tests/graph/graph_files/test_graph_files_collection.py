from pathlib import Path

import pytest

from ra2ce.graph.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.graph.graph_files.graph_files_protocol import GraphFileProtocol
from tests import test_data


class TestGraphFilesCollection:
    def test_initialize(self):
        # 1./2. Define test data / Execute test
        _collection = GraphFilesCollection()

        # 3. Verify results
        assert isinstance(_collection.base_graph, GraphFileProtocol)
        assert _collection.base_graph.file == None

    def test_set_file(self):
        # 1. Define test data
        _file = Path("base_graph.p")
        _type = _file.stem
        _collection = GraphFilesCollection()

        # 2. Execute test
        _collection.set_file(_file)

        # 3. Verify results
        assert _collection.get_file(_type) == _file

    def test_set_file_given_unknown_graph_file_raises_value_error(self):
        # 1. Define test data.
        _unknown_type = "unknown_graphfile.sth"
        _collection = GraphFilesCollection()
        _filepath = test_data.joinpath(_unknown_type)

        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            _collection.set_file(_filepath)

        # 3. Verify expectations.
        assert (
            str(exc_err.value) == f"Unknown graph file type {_filepath.stem} provided."
        )

    def test_set_files(self):
        # 1. Define test data
        _dir = test_data.joinpath("readers_test_data")
        _file = _dir.joinpath("base_graph.p")

        # 2. Execute test
        _collection = GraphFilesCollection.set_files(_dir)

        # 3. Verify results
        assert _collection.base_graph.file == _file

    def test_read_graph(self):
        # 1. Define test data
        _folder = test_data.joinpath("readers_test_data")
        _file = _folder.joinpath("base_graph.p")
        _collection = GraphFilesCollection()

        # 2. Execute test
        _collection.read_graph(_file)

        # 3. Verify results
        assert _collection.base_graph.file == _file
        assert _collection.base_graph.graph

    def test_read_graph_invalid_name(self):
        # 1. Define test data
        _folder = test_data.joinpath("readers_test_data")
        _unknown_file = _folder.joinpath("unknown")
        _collection = GraphFilesCollection()

        # 2. Execute test
        with pytest.raises(ValueError) as exc_err:
            _collection.read_graph(_unknown_file)

        # 3. Verify results
        assert str(exc_err.value) == f"Unknown graph file {_unknown_file} provided."

    def test_has_graphs_without_graphs(self):
        # 1. Define test data
        _collection = GraphFilesCollection()

        # 2. Execute test
        _result = _collection.has_graphs()

        # 3. Verify results
        assert not _result

    def test_has_graphs_with_graphs(self):
        # 1. Define test data
        _folder = test_data.joinpath("readers_test_data")
        _collection = GraphFilesCollection()
        _collection.base_graph.read_graph(_folder)

        # 2. Execute test
        _result = _collection.has_graphs()

        # 3. Verify results
        assert _result

    def test_get_graph_file_given_unknown_type_raises_value_error(self):
        # 1. Define test data.
        _unknown_type = "unknown_graphfile.sth"
        _collection = GraphFilesCollection()

        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            _collection._get_graph_file(_unknown_type)

        # 3. Verify expectations.
        assert (
            str(exc_err.value) == f"Unknown graph file type {_unknown_type} provided."
        )

    def test_set_graph_given_unknown_type_raises_value_error(self):
        # 1. Define test data.
        _unknown_type = "unknown_graphfile.sth"
        _collection = GraphFilesCollection()

        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            _collection.set_graph(_unknown_type, None)

        # 3. Verify expectations.
        assert (
            str(exc_err.value) == f"Unknown graph file type {_unknown_type} provided."
        )

    def test_set_graph_given_known_type_sets_new_graph(self):
        # 1. Define test data.
        _collection = GraphFilesCollection()
        _graph_type = Path(_collection.base_graph.name).stem
        _dummy_graph_value = "JustNotNone"

        assert _collection.base_graph.graph is None

        # 2. Run test.
        _collection.set_graph(_graph_type, _dummy_graph_value)

        # 3. Verify expectations.
        assert _collection.base_graph.graph == _dummy_graph_value
