from pathlib import Path

import pytest

from ra2ce.io.readers.graph_pickle_reader import GraphPickleReader
from tests.io.readers import test_data_readers


class TestGraphPickleReader:
    def test_given_no_path_raises_value_error(self):
        _pickle_path = ""
        with pytest.raises(ValueError) as exc_err:
            GraphPickleReader().read(_pickle_path)
        assert str(exc_err.value) == "No pickle path was provided."

    def test_given_invalid_path_file_raises_value_error(self):
        _pickle_path = Path("not_a_file")
        with pytest.raises(ValueError) as exc_err:
            GraphPickleReader().read(_pickle_path)
        assert str(exc_err.value) == f"No pickle found at path {_pickle_path}"

    def test_given_valid_path_reads_graph(self):
        _pickle_path = test_data_readers / "base_graph.p"
        assert _pickle_path.is_file()

        _graph = GraphPickleReader().read(_pickle_path)
        assert _graph
