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

from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable

from ra2ce.common.configuration.config_data_protocol import ConfigDataProtocol


@runtime_checkable
class ConfigWrapperProtocol(Protocol):  # pragma: no cover
    ini_file: Path
    config_data: Optional[ConfigDataProtocol] = None
    graphs: Optional[dict] = None

    @property
    def root_dir(self) -> Path:
        """
        To be implemented
        """
        pass

    @classmethod
    def from_data(
        cls, ini_file: Path, config_data: ConfigDataProtocol
    ) -> ConfigWrapperProtocol:
        """
        Initializes a `ConfigWrapperProtocol` with the given parameters.

        Args:
            ini_file (Path): Path to the ini file containing the analysis data.
            config_data (IniConfigDataProtocol): Ini data representation.

        Returns:
            ConfigWrapperProtocol: Initialized instance.
        """
        raise NotImplementedError()

    def configure(self) -> None:
        raise NotImplementedError()

    def is_valid(self) -> bool:
        raise NotImplementedError()
