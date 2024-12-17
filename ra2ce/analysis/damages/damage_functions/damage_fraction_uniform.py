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
from scipy.interpolate import interp1d


@dataclass(kw_only=True)
class DamageFractionUniform:
    """
    Uniform: assuming the same curve for
    each road type and lane numbers and any other metadata

    self.raw_data (pd.DataFrame) : Raw data from the csv file
    self.data (pd.DataFrame) : index = hazard severity (e.g. flood depth); column 0 = damage fraction
    """

    name: str
    hazard_unit: str
    data: pd.DataFrame
    origin_path: Path
    interpolator: interp1d = None

    def __post_init__(self):
        self._convert_hazard_severity_unit("m")

    @classmethod
    def from_csv(cls, csv_path: Path, sep: str) -> DamageFractionUniform:
        """Construct object from csv file. Damage curve name is inferred from filename

        Arguments:
            *csv_path* (Path) : Path to the csv file
            *sep* (str) : csv seperator
            *output_unit* (str) : desired output unit

        The CSV file should have the following structure:
         - column 1: hazard severity
         - column 2: damage fraction
         - row 1: column names
         - row 2: unit of column:

        Example:
                +- ------+-------------------------------+
                | depth | damage                        |
                +-------+-------------------------------+
                | cm    | % of total construction costs |
                +-------+-------------------------------+
                | 0     | 0                             |
                +-------+-------------------------------+
                | 50    | 0.25                          |
                +-------+-------------------------------+
                | 100   | 0.42                          |
                +-------+-------------------------------+


        """
        _name = csv_path.stem
        _raw_data = pd.read_csv(csv_path, index_col=0, sep=sep)
        _origin_path = csv_path  # to track the original path from which the object was constructed; maybe also date?

        # identify unit and drop from data
        _hazard_unit = _raw_data.index[0]
        _data = _raw_data.drop(
            _hazard_unit
        )  # Todo: This could also be a series instead of DataFrame

        # convert data to floats
        _data = _data.astype("float")
        _data.index = _data.index.astype("float")

        return cls(
            name=_name, hazard_unit=_hazard_unit, data=_data, origin_path=_origin_path
        )

    def _convert_hazard_severity_unit(self, desired_unit: str) -> None:
        """Converts hazard severity values to a different unit
        Arguments:
            self.hazard_unit - implicit (string)
            *desired_unit* (string)

        Effect: converts the values in self.data; and sets the new damage_unit to the desired unit

        """
        if desired_unit == self.hazard_unit:
            logging.info(
                "Damage units are already in the desired format %s", desired_unit
            )
            return None

        if self.hazard_unit == "cm" and desired_unit == "m":
            scaling_factor = 1 / 100
            self.data.index = self.data.index * scaling_factor
            logging.info(
                "Hazard severity from %s data was scaled by a factor %s, to convert from %s to %s",
                self.origin_path,
                scaling_factor,
                self.hazard_unit,
                desired_unit,
            )
            self.damage_unit = desired_unit
            return None
        else:
            logging.warning(
                "Hazard severity scaling from %s to %s is not  supported",
                self.hazard_unit,
                desired_unit,
            )
            return None

    def create_interpolator(self):
        """Create interpolator object from loaded data
        sets result to self.interpolator (Scipy interp1d)
        """
        x_values = self.data.index.values
        y_values = self.data.values[:, 0]

        self.interpolator = interp1d(
            x=x_values,
            y=y_values,
            fill_value=(
                y_values[0],
                y_values[-1],
            ),  # fraction damage (y) if hazard severity (x) is outside curve range
            bounds_error=False,
        )

        return None

    def __repr__(self):
        if self.interpolator:
            string = (
                "DamageFractionUniform with name: "
                + self.name
                + " interpolator: {}".format(
                    list(zip(self.interpolator.y, self.interpolator.x))
                )
            )
        else:
            string = "DamageFractionUniform with name: " + self.name
        return string
