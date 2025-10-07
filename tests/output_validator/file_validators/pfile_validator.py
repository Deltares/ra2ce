import pickle
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import pandas as pd

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


@dataclass
class PfileValidator(FileValidatorProtocol):
    reference_file: Path
    result_file: Path

    def __post_init__(self) -> None:
        def _get_normalized_content(file_path: Path) -> pd.DataFrame:
            with open(file_path, "rb") as _file_path:
                _graph = pickle.load(_file_path)
            assert isinstance(_graph, nx.Graph)
            return _graph

        _graph_ref = _get_normalized_content(self.reference_file)
        _graph_res = _get_normalized_content(self.result_file)

        if nx.is_isomorphic(_graph_ref, _graph_res):
            return

        raise AssertionError(f"P file {self.result_file.name} differs in content.")
