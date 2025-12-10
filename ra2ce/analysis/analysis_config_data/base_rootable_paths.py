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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseRootablePaths(ABC):

    def _get_new_root(self, old_root: Path, new_root: Path) -> Optional[Path]:
        # Rewrite the path to the new root
        if not old_root:
            return None
        _orig_parts = old_root.parts
        _rel_path = Path(*_orig_parts[len(old_root.parts) :])
        return new_root.joinpath(_rel_path)

    @abstractmethod
    def reroot_fields(self, old_root: Path, new_root: Path):
        """
        Rewrites the paths of the input files in the config data instance to be relative to the new root path.

        Args:
            new_root (Path): The new root path to which the input file paths should be adjusted.
        """
        pass