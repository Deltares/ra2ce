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
        def find_damage_functions(folder: Path) -> dict[str, Path]:
            return {
                subfolder.stem: subfolder
                for subfolder in folder.iterdir()
                if subfolder.is_dir()
            }

        _damage_functions: dict[str, DamageFunctionByRoadTypeByLane] = dict()
        for _name, _path in find_damage_functions(file_path).items():
            _damage_functions[_name] = DamageFunctionByRoadTypeByLane.from_input_folder(
                _name, _path
            )

        return ManualDamageFunctions(damage_functions=_damage_functions)
