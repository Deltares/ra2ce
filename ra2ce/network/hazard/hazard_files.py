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

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HazardFiles:
    tif: list[Path] = field(default_factory=list)
    gpkg: list[Path] = field(default_factory=list)
    table: list[Path] = field(default_factory=list)

    @classmethod
    def from_hazard_map(cls, hazard_map: list[Path]) -> HazardFiles:
        """
        Create a HazardFiles object from a list of hazard map files.

        Args:
            hazard_map (list[Path]): _description_

        Returns:
            HazardFiles: _description_
        """

        def _get_filtered_files(*suffix) -> list[Path]:
            _filter = lambda x: x.suffix in list(suffix)
            return list(filter(_filter, hazard_map))

        return cls(
            tif=_get_filtered_files(".tif"),
            gpkg=_get_filtered_files(".gpkg"),
            table=_get_filtered_files(".csv"),
        )
