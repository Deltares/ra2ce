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


from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FileReaderProtocol(Protocol):
    def read(self, file_path: Path) -> Any:
        """
        Reads from a given file and converts the data into `Any` type.

        Args:
            file_path (Path): Path to a file containing data to be read.

        Returns:
            Any: Object mapped from the data in the file.
        """
        pass
