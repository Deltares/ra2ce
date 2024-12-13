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

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(kw_only=True)
class MaxDamage:
    """
    Max damage per RoadType and per Lane
    """

    name: str
    damage_unit: str
    data: pd.DataFrame
    origin_path: Path = None

    def __post_init__(self):
        self._convert_length_unit("euro/m")

    @classmethod
    def from_csv(cls, csv_path: Path, sep: str) -> MaxDamage:
        """Construct object from csv file. Damage curve name is inferred from filename

        The first row describes the lane numbers per column and should have 'Road_type \ lanes' as index/first value.
        Assume road types are in the rows; lane numbers in the columns.
        The second row has the units per column, and should have 'unit' as index/first value
        the rest of the rows contains the different road types as index/first value; and the costs as values

        Arguments:
            *csv_* (Path) : Path to the csv file
            *sep* (str) : csv seperator
        """
        _name = csv_path.stem
        _raw_data = pd.read_csv(csv_path, index_col=r"Road_type \ lanes", sep=sep)
        _origin_path = csv_path  # to track the original path from which the object was constructed; maybe also date?

        ###Determine units
        units = _raw_data.loc["unit", :].unique()  # identify the unique units
        assert (
            len(units) == 1
        ), "Columns in the max damage csv seem to have different units, ra2ce cannot handle this"
        # case only one unique unit is identified
        _damage_unit = units[
            0
        ]  # should have the structure 'x/y' , e.g. euro/m, dollar/yard

        _data = _raw_data.drop("unit")
        _data = _data.astype("float")

        # assumes that the columns containst the lanes
        _data.columns = _data.columns.astype("int")

        return cls(
            name=_name,
            damage_unit=_damage_unit,
            data=_data,
            origin_path=_origin_path,
        )

    def _convert_length_unit(self, desired_unit: str):
        """Converts max damage values to a different unit
        Arguments:
            self.damage_unit (implicit)
            *desired_unit* (string)

        Effect: converts the values in self.data; and sets the new damage_unit

        """
        if desired_unit == self.damage_unit:
            return

        original_length_unit = self.damage_unit.split("/")[1]
        target_length_unit = desired_unit.split("/")[1]

        if original_length_unit != "km" or target_length_unit != "m":
            # We currently only support from 'km' to 'm'
            logging.warning(
                "Damage scaling from %s to %s is not supported",
                self.damage_unit,
                desired_unit,
            )
            return

        scaling_factor = 1 / 1000
        self.data = self.data * scaling_factor
        logging.info(
            "Damage data from %s was scaled by a factor %s, to convert from %s to %s",
            self.origin_path,
            scaling_factor,
            self.damage_unit,
            desired_unit,
        )
        self.damage_unit = desired_unit
