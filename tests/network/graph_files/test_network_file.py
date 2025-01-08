from pathlib import Path

import pytest
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

    @pytest.mark.parametrize("name", ["base_network.feather", "base_graph_edges.gpkg"])
    def test_read_graph(self, graph_folder: Path, name: str):
        # 1. Define test data
        _file = graph_folder.joinpath(name)
        _nf = NetworkFile(name=name)

        # 2. Execute test
        _nf.read_graph(graph_folder)

        # 3. Verify results
        assert _nf.file == _file
        assert _nf.graph is not None

    def test_read_graph_unknown_type_throws(self, graph_folder: Path):
        # 1. Define test data
        _name = "base_graph.p"
        _nf = NetworkFile(name=_name)

        # 2. Execute test
        with pytest.raises(ValueError) as exc:
            _nf.read_graph(graph_folder)

        # 3. Verify results
        assert exc.match("Unknown file type")

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
