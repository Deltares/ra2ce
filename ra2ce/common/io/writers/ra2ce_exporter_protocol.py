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
class Ra2ceExporterProtocol(Protocol):
    def export(self, export_path: Path, export_data: Any) -> None:  # pragma: no cover
        """
        Exports the given data to the given path.

        Args:
            export_path (Path): File path where to save the `export_data`.
            export_data (Any): Data to be exported.
        """
        pass
