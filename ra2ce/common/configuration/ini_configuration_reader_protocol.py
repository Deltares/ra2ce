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
from typing import Protocol, runtime_checkable

from ra2ce.common.configuration.config_data_protocol import ConfigDataProtocol
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol


@runtime_checkable
class ConfigDataReaderProtocol(FileReaderProtocol, Protocol):  # pragma: no cover
    def read(self, ini_file: Path) -> ConfigDataProtocol:
        """
        Reads the given `*.ini` file and if possible converts it into a `IniConfigDataProtocol` object.

        Args:
            ini_file (Path): Ini file to be mapped into a `IniConfigDataProtocol`.

        Returns:
            ConfigWrapperProtocol: Resulting mapped object from the configuration data in the given file.
        """
        pass
