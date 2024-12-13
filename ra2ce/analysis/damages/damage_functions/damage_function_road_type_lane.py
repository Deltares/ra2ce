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

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ra2ce.analysis.damages.damage_functions.damage_fraction_uniform import (
    DamageFractionUniform,
)
from ra2ce.analysis.damages.damage_functions.max_damage import MaxDamage


@dataclass(kw_only=True)
class DamageFunctionByRoadTypeByLane:
    """
    A damage function that has different max damages per road type, but a uniform damage_fraction curve

    The attributes need to be of the type:
    self.max_damage (MaxDamage)
    self.damage_fraction (DamageFractionUniform)
    name (str)
    """

    max_damage: MaxDamage
    damage_fraction: DamageFractionUniform
    name: str

    @property
    def prefix(self) -> str:
        return self.name[0:2] if len(self.name) > 2 else self.name

    @classmethod
    def from_input_folder(
        cls, name: str, folder_path: Path
    ) -> DamageFunctionByRoadTypeByLane:
        """Construct a set of damage functions from csv files located in the folder_path

        Arguments:
            name (str) : name of the damage function
            folder_path (Pathlib Path) : path to folder where csv files can be found
        """

        def find_unique_csv_file(folder_path: Path, part_of_filename: str) -> Path:
            """
            Find unique csv file in a folder, with a given part_of_filename
            Raises a warning if no file can be found, and an error if more than one file is found
            """
            result = []
            for file in folder_path.iterdir():
                if (part_of_filename in file.stem) and (file.suffix == ".csv"):
                    result.append(file)
            if len(result) > 1:
                raise ValueError(
                    "Found more then one damage file in {}".format(folder_path)
                )
            elif len(result) == 0:
                raise ValueError(
                    "Did not find any damage file in {}".format(folder_path)
                )

            return result[0]

        # Load the max_damage object
        max_dam_path = find_unique_csv_file(folder_path, "max_damage")
        max_damage = MaxDamage.from_csv(max_dam_path, ";")

        # Load the damage fraction function
        # search in the folder for something *damage_fraction
        dam_fraction_path = find_unique_csv_file(folder_path, "hazard_severity")
        damage_fraction = DamageFractionUniform.from_csv(dam_fraction_path, sep=";")

        damage_fraction.create_interpolator()

        return cls(max_damage=max_damage, damage_fraction=damage_fraction, name=name)

    # Todo: these two below functions are maybe better implemented at a lower level?
    def add_max_damage(self, df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        """ "Ads the max damage value to the dataframe"""
        cols = df.columns
        assert "road_type" in cols, "no column 'road type' in df"
        assert "lanes" in cols, "no column 'lanes in df"

        max_damage_data = self.max_damage.data
        df["{}_temp_max_dam".format(prefix)] = max_damage_data.lookup(
            df["infra_type"], df["lanes"]
        )
        return df

    def calculate_damage(
        self,
        df: pd.DataFrame,
        damage_function_prefix: str,
        hazard_prefix: str,
        event_prefix: str,
    ) -> pd.DataFrame:
        """
        Calculates the damage for one event. The prefixes are used to find/set the right df columns.

        Args:
            df (pd.DataFrame): dataframe with road network data.
            damage_function_prefix (str): prefix to identify the right damage function e.g. 'A'.
            hazard_prefix (str): prefix to identify the right hazard e.g. 'F'.
            event_prefix (str): prefix to identify the right event, e.g. 'EV1'

        Returns:
            pd.DataFrame: dataframe data with the damage calculation added as new column
        """

        interpolator = (
            self.damage_fraction.interpolator
        )  # get the interpolator function

        # Find correct columns in dataframe
        result_col = "dam_{}_{}".format(event_prefix, damage_function_prefix)
        max_dam_col = "{}_temp_max_dam".format(damage_function_prefix)
        hazard_severity_col = "{}_{}_me".format(
            hazard_prefix, event_prefix
        )  # mean is hardcoded now
        hazard_fraction_col = "{}_{}_fr".format(
            hazard_prefix, event_prefix
        )  # fraction column is hardcoded

        df[result_col] = round(
            df[max_dam_col].astype(float)  # max damage (euro/m)
            * interpolator(df[hazard_severity_col].astype(float))  # damage curve  (-)
            * df["length"]  # segment length (m)
            * df[hazard_fraction_col],
            0,
        )  # round to whole numbers
        return df
