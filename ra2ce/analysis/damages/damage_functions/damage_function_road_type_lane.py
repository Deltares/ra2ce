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
from typing import Any, Hashable, Optional

import pandas as pd

import warnings


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
    allowed_asset_types: set[str]

    @property
    def prefix(self) -> str:
        return self.name[0:2] if len(self.name) > 2 else self.name

    @classmethod
    def from_input_folder(
        cls, name: str, folder_path: Path, allowed_asset_types: Optional[set[str]]
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

        return cls(
            max_damage=max_damage, damage_fraction=damage_fraction, name=name, allowed_asset_types=allowed_asset_types
        )

    # Todo: these two below functions are maybe better implemented at a lower level?
    def add_max_damage(self, df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        """ "Ads the max damage value to the dataframe"""
        cols = df.columns
        assert "road_type" in cols, "no column 'road type' in df"
        assert "lanes" in cols, "no column 'lanes in df"

        max_damage_data = self.max_damage.data

        # Validate index asset types
        norm_allowed = {a.strip().casefold() for a in self.allowed_asset_types}
        index_values = max_damage_data.index
        invalid = sorted({
            str(idx).strip().casefold()
            for idx in index_values
            if str(idx).strip().casefold() not in norm_allowed
        })
        if invalid:
            warnings.warn(
                "Unsupported asset type(s) in max_damage_data index: "
                f"{', '.join(invalid)}. Allowed: {', '.join(sorted(norm_allowed))}",
                category=UserWarning,
                stacklevel=2,  # points the warning at the caller's line in the stack
            )

        # Flatten max_damage_data into a Series with MultiIndex (infra_type, lanes)
        max_damage_series = (
            max_damage_data
            .stack()  # turns wide columns into rows
            .rename("max_damage")
        )
        # Now the index is ('Road_type \ lanes', lanes)

        # Map into df
        df[f"{prefix}_temp_max_dam"] = df.set_index(["infra_type", "lanes"]).index.map(max_damage_series)

        return df

    def calculate_damage(
        self,
        df: pd.DataFrame,
        damage_function_prefix: str,
        hazard_prefix: str,
        event_prefix: str,
        asset_type: Optional[str] = None,   # <-- NEW PARAM
    ) -> pd.DataFrame:
        """
        Calculates the damage for one event, but only for rows that match the asset filter:
          - If `asset_type` ∈ {"bridge", "viaduct", "tunnel"}: only rows with that `infra_type`.
          - Else (asset_type is None or other like 'standard'): only rows whose `infra_type`
            is NOT in the allowed set.

        The prefixes are used to find/set the right df columns.
        """
        interpolator = self.damage_fraction.interpolator

        result_col = f"dam_{event_prefix}_{damage_function_prefix}"
        max_dam_col = f"{damage_function_prefix}_temp_max_dam"
        hazard_severity_col = f"{hazard_prefix}_{event_prefix}_me"  # mean
        hazard_fraction_col = f"{hazard_prefix}_{event_prefix}_fr"  # fraction

        infra = df["infra_type"].astype(str).str.lower()
        current = (asset_type or "").strip().lower()

        if current in self.allowed_asset_types:
            row_mask = infra.eq(current)
        else:
            # 'standard' / 'non' / None => rows that are not bridge/viaduct/tunnel
            row_mask = ~infra.isin(self.allowed_asset_types)

        if not row_mask.any():
            # No rows to compute for this asset filter
            return df

        # Compute only on the masked subset
        values = (
            df.loc[row_mask, max_dam_col].astype(float)
            * interpolator(df.loc[row_mask, hazard_severity_col].astype(float))
            * df.loc[row_mask, "length"]
            * df.loc[row_mask, hazard_fraction_col]
        ).round(0)

        df.loc[row_mask, result_col] = values
        return df