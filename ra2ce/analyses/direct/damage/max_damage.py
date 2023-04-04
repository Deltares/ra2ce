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

import pandas as pd


class MaxDamageByRoadTypeByLane:
    """
    Max damage per RoadType and per Lane

    Attributes:
        self.name (str) : Name of the damage curve
        self.data (pd.DataFrame) : columns contain number of lanes; rows contain the road types

    Optional attributes:
        self.origin_path (Path) : Path to the file from which the function was constructed
        self.raw_data : The raw data read from the input file


    """

    def __init__(self, name=None, damage_unit=None):
        self.name = name
        self.damage_unit = damage_unit

    def from_csv(self, path: Path, sep=",") -> None:
        """Construct object from csv file. Damage curve name is inferred from filename

        The first row describe the lane numbers per column; and should have 'Road_type \ lanes' as index/first value
        The second row has the units per column, and should have 'unit' as index/first value
        the rest of the rows contains the different road types as index/first value; and the costs as values

        Arguments:
            *path* (Path) : Path to the csv file
            *sep* (str) : csv seperator
            *output_unit* (str) : desired output unit (default = 'euro/m')

        """
        self.name = path.stem
        self.raw_data = pd.read_csv(path, index_col="Road_type \ lanes", sep=sep)
        self.origin_path = path  # to track the original path from which the object was constructed; maybe also date?

        ###Determine units
        units = self.raw_data.loc["unit", :].unique()  # identify the unique units
        assert (
            len(units) == 1
        ), "Columns in the max damage csv seem to have different units, ra2ce cannot handle this"
        # case only one unique unit is identified
        self.damage_unit = units[
            0
        ]  # should have the structure 'x/y' , e.g. euro/m, dollar/yard

        self.data = self.raw_data.drop("unit")
        self.data = self.data.astype("float")

        # assume road types are in the rows; lane numbers in the columns
        self.road_types = list(self.data.index)  # to method
        # assumes that the columns containst the lanes
        self.data.columns = self.data.columns.astype("int")

        if self.damage_unit != "output_unit":
            self.convert_length_unit()  # convert the unit

    def convert_length_unit(self, desired_unit="euro/m"):
        """Converts max damage values to a different unit
        Arguments:
            self.damage_unit (implicit)
            *desired_unit* (string)

        Effect: converts the values in self.data; and sets the new damage_unit

        """
        if desired_unit == self.damage_unit:
            logging.info("Input damage units are already in the desired format")
            return

        original_length_unit = self.damage_unit.split("/")[1]
        target_length_unit = desired_unit.split("/")[1]

        if original_length_unit != "km" or target_length_unit != "m":
            # We currently only support from 'km' to 'm'
            logging.warning(
                "Damage scaling from {} to {} is not supported".format(
                    self.damage_unit, desired_unit
                )
            )
            return

        scaling_factor = 1 / 1000
        self.data = self.data * scaling_factor
        logging.info(
            "Damage data from {} was scaled by a factor {}, to convert from {} to {}".format(
                self.origin_path, scaling_factor, self.damage_unit, desired_unit
            )
        )
        self.damage_unit = desired_unit
