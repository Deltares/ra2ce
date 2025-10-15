import pickle
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import pytest

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


@dataclass
class PfileValidator(FileValidatorProtocol):
    reference_file: Path
    result_file: Path

    def __post_init__(self) -> None:
        def _get_normalized_content(file_path: Path) -> nx.Graph:
            with open(file_path, "rb") as _file_path:
                _graph = pickle.load(_file_path)
            assert isinstance(_graph, nx.Graph)
            return _graph

        _graph_ref = _get_normalized_content(self.reference_file)
        _graph_res = _get_normalized_content(self.result_file)

        if nx.is_isomorphic(_graph_ref, _graph_res):
            return

        # Custom isomorphism check on edges
        _total_edges = len(_graph_ref.edges)
        _total_matching_edges = 0
        for u_r, v_r in _graph_ref.edges():
            for u_s, v_s in _graph_res.edges():
                if u_r == u_s and v_r == v_s:
                    _total_matching_edges += 1
                    break

        # Allow for 5% deviation in number of matching edges
        if _total_matching_edges == pytest.approx(_total_edges, rel=5e-2):
            return

        raise AssertionError(f"P file {self.result_file.name} deviates in content.")
