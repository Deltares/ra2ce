import pickle
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import numpy as np

from tests.output_validator.file_validators.file_validator_protocol import (
    FileValidatorProtocol,
)


@dataclass
class PfileValidator(FileValidatorProtocol):
    reference_file: Path
    result_file: Path

    def __post_init__(self) -> None:
        def _get_normalized_content(file_path: Path) -> np.ndarray:
            with open(file_path, "rb") as _file_path:
                _graph = pickle.load(_file_path)
            assert isinstance(_graph, nx.Graph)
            return nx.to_numpy_array(_graph, weight="weight")

        _nodes_ref = _get_normalized_content(self.reference_file)
        _nodes_res = _get_normalized_content(self.result_file)

        if np.allclose(_nodes_ref, _nodes_res, atol=1e-3):
            return

        raise AssertionError(f"P file {self.result_file.name} deviates in content.")
