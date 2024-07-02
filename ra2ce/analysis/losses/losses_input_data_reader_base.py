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
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd

from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol


class LossesInputDataReaderBase(ABC, FileReaderProtocol):
    """
    Base class for reading losses input data from a csv file.
    """

    csv_columns: list[str] = []
    separator: str = ";"
    object_type: type[Any]

    @abstractmethod
    def _parse_df(self, df: pd.DataFrame) -> Any:
        """
        Abstract method to parse the data from a DataFrame.

        Args:
            df (pd.DataFrame): The parsed data from the csv file.

        Returns:
            Any: Dataclass containing the parsed data.
        """
        pass

    def read(self, file_path: Path | None) -> Any:
        if not file_path or not file_path.exists():
            logging.warning(
                "No csv file found at %s. Using default values for %s.",
                file_path,
                self.object_type,
            )
            return self.object_type()

        _df = pd.read_csv(file_path, sep=self.separator, on_bad_lines="skip")
        if "geometry" in _df.columns:
            raise ValueError(
                f"The csv file in {file_path} should not have a geometry column"
            )

        if not all(col in _df.columns for col in self.csv_columns):
            raise ValueError(
                f"The csv file in {file_path} should have columns {', '.join(self.csv_columns)}",
            )

        return self._parse_df(_df)
