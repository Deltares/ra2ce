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

from ra2ce.analysis.damages.damage_functions.damage_function_road_type_lane import (
    DamageFunctionByRoadTypeByLane,
)
from ra2ce.analysis.damages.damage_functions.manual_damage_functions import (
    ManualDamageFunctions,
)
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol


class ManualDamageFunctionsReader(FileReaderProtocol):
    """
    Reader class for the manual damage functions.
    """

    def read(self, file_path: Path) -> ManualDamageFunctions:
        """
        Read the manual damage functions from the given folder.
        The folder should contain subfolders with the damage functions.
        Each damage functions is constructed by reading the csv files for the max damage and damage fraction.

        Args:
            file_path (Path): Pathm to the folder containing the manual damage functions folders

        Returns:
            ManualDamageFunctions: The manual damage functions
        """
        # Find subfolders with the damage functions
        _damage_function_folders = {
            subfolder.stem: subfolder
            for subfolder in file_path.iterdir()
            if subfolder.is_dir()
        }

        # Read the damage functions from the subfolders
        return ManualDamageFunctions(
            damage_functions={
                _name: DamageFunctionByRoadTypeByLane.from_input_folder(_name, _path)
                for _name, _path in _damage_function_folders.items()
            }
        )
