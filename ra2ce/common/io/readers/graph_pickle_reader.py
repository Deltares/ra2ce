"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import logging
import pickle
from pathlib import Path
from typing import Any

from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol


class GraphPickleReader(FileReaderProtocol):
    def read(self, pickle_path: Path) -> Any:
        _read_graph = None
        if not pickle_path:
            raise ValueError("No pickle path was provided.")

        if not pickle_path.is_file():
            _error_mssg = f"No pickle found at path {pickle_path}"
            logging.error(_error_mssg)
            raise ValueError(_error_mssg)

        with open(pickle_path, "rb") as f:
            _read_graph = pickle.load(f)

        return _read_graph
