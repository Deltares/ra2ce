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


class DamageFractionUniform:
    """
    Uniform: assuming the same curve for
    each road type and lane numbers and any other metadata


    self.raw_data (pd.DataFrame) : Raw data from the csv file
    self.data (pd.DataFrame) : index = hazard severity (e.g. flood depth); column 0 = damage fraction

    """

    def __init__(self, name=None, hazard_unit=None):
        self.name = name
        self.hazard_unit = hazard_unit
        self.interpolator = None

    def from_csv(self, path: Path, sep=",") -> None:
        """Construct object from csv file. Damage curve name is inferred from filename

        Arguments:
            *path* (Path) : Path to the csv file
            *sep* (str) : csv seperator
            *output_unit* (str) : desired output unit (default = 'm')

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
        self.name = path.stem
        self.raw_data = pd.read_csv(path, index_col=0, sep=sep)
        self.origin_path = path  # to track the original path from which the object was constructed; maybe also date?

        # identify unit and drop from data
        self.hazard_unit = self.raw_data.index[0]
        self.data = self.raw_data.drop(
            self.hazard_unit
        )  # Todo: This could also be a series instead of DataFrame

        # convert data to floats
        self.data = self.data.astype("float")
        self.data.index = self.data.index.astype("float")

        self.convert_hazard_severity_unit()

    def convert_hazard_severity_unit(self, desired_unit="m") -> None:
        """Converts hazard severity values to a different unit
        Arguments:
            self.hazard_unit - implicit (string)
            *desired_unit* (string)

        Effect: converts the values in self.data; and sets the new damage_unit to the desired unit

        """
        if desired_unit == self.hazard_unit:
            logging.info(
                "Damage units are already in the desired format {}".format(desired_unit)
            )
            return None

        if self.hazard_unit == "cm" and desired_unit == "m":
            scaling_factor = 1 / 100
            self.data.index = self.data.index * scaling_factor
            logging.info(
                "Hazard severity from {} data was scaled by a factor {}, to convert from {} to {}".format(
                    self.origin_path, scaling_factor, self.hazard_unit, desired_unit
                )
            )
            self.damage_unit = desired_unit
            return None
        else:
            logging.warning(
                "Hazard severity scaling from {} to {} is not  supported".format(
                    self.hazard_unit, desired_unit
                )
            )
            return None

    def create_interpolator(self):
        """Create interpolator object from loaded data
        sets result to self.interpolator (Scipy interp1d)
        """
        from scipy.interpolate import interp1d

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
