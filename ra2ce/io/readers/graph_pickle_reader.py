import logging
import pickle
from pathlib import Path
from typing import Any

from ra2ce.io.readers.file_reader_protocol import FileReaderProtocol


class GraphPickleReader(FileReaderProtocol):
    def read(self, pickle_path: Path) -> Any:
        _read_graph = None
        if not pickle_path:
            raise ValueError(f"No pickle path was provided.")

        if not pickle_path.is_file():
            _error_mssg = f"No pickle found at path {pickle_path}"
            logging.error(_error_mssg)
            raise ValueError(_error_mssg)

        with open(pickle_path, "rb") as f:
            _read_graph = pickle.load(f)

        return _read_graph
