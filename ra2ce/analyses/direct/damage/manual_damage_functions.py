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
from pathlib import Path

from ra2ce.analyses.direct.damage.damage_function_road_type_lane import (
    DamageFunctionByRoadTypeByLane,
)


class ManualDamageFunctions:
    """ "
    This class keeps an overview of the manual damage functions

    Default behaviour is to find, load and apply all available functions
    At 22 sept 2022: only implemented workflow for DamageFunction_by_RoadType_by_Lane
    """

    def __init__(self):
        self.available = (
            {}
        )  # keys = name of the available functions; values = paths to the folder
        self.loaded = []  # List of DamageFunction objects (or child classes

    def find_damage_functions(self, folder: Path) -> None:
        """Find all available damage functions in the specified folder"""
        assert folder.exists(), "Folder {} does not contain damage functions".format(
            folder
        )
        for subfolder in folder.iterdir():  # Subfolders contain the damage curves
            if subfolder.is_dir():
                # print(subfolder.stem,subfolder)
                self.available[subfolder.stem] = subfolder
        logging.info(
            "Found {} manual damage curves: \n {}".format(
                len(self.available.keys()), list(self.available.keys())
            )
        )
        return None

    def load_damage_functions(self):
        """ "Load damage functions in Ra2Ce"""
        for name, damage_dir in self.available.items():
            damage_function = DamageFunctionByRoadTypeByLane(name=name)
            damage_function.from_input_folder(damage_dir)
            damage_function.set_prefix()
            self.loaded.append(damage_function)
            logging.info(
                "Damage function '{}' loaded from folder {}".format(
                    damage_function.name, damage_dir
                )
            )
