import logging
import pickle
from pathlib import Path
from typing import Any


class GraphPickleReader:
    def read(self, pickle_path: Path) -> Any:
        _read_graph = None
        if not pickle_path:
            raise ValueError(f"No pickle path was provided")
        if not pickle_path.is_file():
            logging.warning(f"No pickle found at path {pickle_path}")
            return None

        with open(pickle_path, "rb") as f:
            _read_graph = pickle.load(f)

        return _read_graph
