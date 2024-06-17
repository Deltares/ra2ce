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

import os
from collections import OrderedDict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame
from scipy.interpolate import interp1d


def dataframe_lookup(row: pd.Series, lookup_df: DataFrame, columns: list) -> Any:
    row_values = [row[column] for column in columns]
    return lookup_df.loc[tuple(row_values)]


class LookUp:
    """ " This namespace contains several lookup tables, used e.g. for road damage calculation."""

    @staticmethod
    def road_mapping():
        """Mapping of OSM road infrastructure types"""

        mapping_dict = {
            "disused": "none",
            "dummy": "none",
            "planned": "none",
            "platform": "none",
            "unsurfaced": "track",
            "traffic_island": "other",
            "razed": "none",
            "abandoned": "none",
            "services": "none",
            "proposed": "none",
            "corridor": "track",
            "bus_guideway": "other",
            "bus_stop": "other",
            "rest_area": "other",
            "yes": "other",
            "trail": "track",
            "escape": "other",
            "raceway": "other",
            "emergency_access_point": "none",
            "emergency_bay": "other",
            "construction": "other",
            "bridleway": "none",
            "cycleway": "other",
            "footway": "track",
            "living_street": "other",
            "path": "track",
            "pedestrian": "other",
            "primary": "primary",
            "primary_link": "primary",
            "residential": "other",
            "road": "other",
            "secondary": "secondary",
            "secondary_link": "secondary",
            "service": "other",
            "steps": "none",
            "tertiary": "tertiary",
            "tertiary_link": "tertiary",
            "track": "track",
            "unclassified": "other",
            "trunk": "trunk",
            "motorway": "motorway",
            "trunk_link": "trunk",
            "motorway_link": "motorway",
            "elevator": "none",
            "access": "none",
            "crossing": "other",
            "mini_roundabout": "other",
            "passing_place": "other",
            "turning_circle": "other",
            "motorway_junction": "motorway",
        }
        return mapping_dict

    @staticmethod
    def road_lanes():
        """Mapping of road lanes, this is used as a default in case of missings. Number of lanes differ per country."""

        return OrderedDict(
            [
                (
                    "AL",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 1),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "AT",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 1),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "BE",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "BG",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "CH",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 1),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "CZ",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "DE",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "DK",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "EE",
                    OrderedDict(
                        [
                            ("motorway", 1),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "EL",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "ES",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "FI",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "FR",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "HR",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "HU",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "IE",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 1),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "IS",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 1),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "IT",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "LT",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "LU",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 3),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "LV",
                    OrderedDict(
                        [
                            ("motorway", 1),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "LI",
                    OrderedDict(
                        [
                            ("motorway", 1),
                            ("trunk", 1),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "ME",
                    OrderedDict(
                        [
                            ("motorway", 1),
                            ("trunk", 1),
                            ("primary", 2),
                            ("secondary", 1),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "MK",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "NL",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 1),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "NO",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 1),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "PL",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "PT",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "RO",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "RS",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "SE",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "SI",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "SK",
                    OrderedDict(
                        [
                            ("motorway", 2),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "TR",
                    OrderedDict(
                        [
                            ("motorway", 3),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
                (
                    "UK",
                    OrderedDict(
                        [
                            ("motorway", 3),
                            ("trunk", 2),
                            ("primary", 2),
                            ("secondary", 2),
                            ("tertiary", 2),
                            ("track", 1),
                            ("other", 1),
                            ("none", 1),
                        ]
                    ),
                ),
            ]
        )

    @staticmethod
    def get_lane_number_damage_correction():
        """Lookup table for correction factor of damage for lanes"""
        lookup_dict = OrderedDict(
            [
                ("motorway", {1: 0.75, 2: 1.0, 3: 1.25, 4: 1.5, 5: 1.75, 6: 2.0}),
                ("trunk", {1: 0.75, 2: 1.0, 3: 1.25, 4: 1.5, 5: 1.75, 6: 2.0}),
                ("primary", {1: 0.75, 2: 1.0, 3: 1.25, 4: 1.5, 5: 1.75, 6: 2.0}),
                ("secondary", {1: 0.75, 2: 1.0, 3: 1.25, 4: 1.5, 5: 1.75, 6: 2.0}),
                ("tertiary", {1: 0.75, 2: 1.0, 3: 1.5, 4: 1.75, 5: 2.0, 6: 2.25}),
                ("other", {1: 1.0, 2: 1.25, 3: 1.5, 4: 1.75, 5: 2.0, 6: 2.25}),
                ("track", {1: 1.0, 2: 1.25, 3: 1.5, 4: 1.75, 5: 2.0, 6: 2.25}),
                ("none", {1: 1.0, 2: 1.25, 3: 1.5, 4: 1.75, 5: 2.0, 6: 2.25}),
            ]
        )

        return lookup_dict

    @staticmethod
    def max_damages():
        """Lookup table for max damages"""
        return OrderedDict(
            [
                (
                    "Lower",
                    OrderedDict(
                        [
                            ("motorway", 1750000),
                            ("trunk", 1250000),
                            ("primary", 1000000),
                            ("secondary", 500000),
                            ("tertiary", 200000),
                            ("other", 100000),
                            ("track", 20000),
                            ("none", 0),
                        ]
                    ),
                ),
                (
                    "Upper",
                    OrderedDict(
                        [
                            ("motorway", 17500000),
                            ("trunk", 3750000),
                            ("primary", 3000000),
                            ("secondary", 1500000),
                            ("tertiary", 600000),
                            ("other", 300000),
                            ("track", 50000),
                            ("none", 0),
                        ]
                    ),
                ),
            ]
        )

    @staticmethod
    def get_max_damages_osd():
        """Lookup table for max damages of the OSdaMage damage functions"""

        # Note that these values have been converted to euro/m road length
        return OrderedDict(
            [
                (
                    "Lower",
                    OrderedDict(
                        [
                            ("motorway", 1750),
                            ("trunk", 1250),
                            ("primary", 1000),
                            ("secondary", 500),
                            ("tertiary", 200),
                            ("other", 100),
                            ("track", 20),
                            ("none", 0),
                        ]
                    ),
                ),
                (
                    "Upper",
                    OrderedDict(
                        [
                            ("motorway", 17500),
                            ("trunk", 3750),
                            ("primary", 3000),
                            ("secondary", 1500),
                            ("tertiary", 600),
                            ("other", 300),
                            ("track", 50),
                            ("none", 0),
                        ]
                    ),
                ),
            ]
        )

    @staticmethod
    def get_max_damages_huizinga() -> dict:
        """Lookup table for max damages calculated with huizinga for number of lanes

        Output: dict:
         - road types are keys
         - max damages in euro / m road length
        """

        # Note, these values are in euro/km; while RA2CE standard unit is euro/m length

        lookup_dict = OrderedDict(
            [
                (
                    "motorway",
                    {1: 175000, 2: 350000, 3: 450000, 4: 550000, 5: 650000, 6: 750000},
                ),
                (
                    "trunk",
                    {1: 175000, 2: 300000, 3: 400000, 4: 475000, 5: 575000, 6: 650000},
                ),
                (
                    "primary",
                    {1: 125000, 2: 250000, 3: 325000, 4: 425000, 5: 500000, 6: 575000},
                ),
                (
                    "secondary",
                    {1: 125000, 2: 225000, 3: 300000, 4: 400000, 5: 475000, 6: 550000},
                ),
                (
                    "tertiary",
                    {1: 100000, 2: 175000, 3: 250000, 4: 350000, 5: 425000, 6: 500000},
                ),
                (
                    "track",
                    {1: 75000, 2: 150000, 3: 225000, 4: 300000, 5: 375000, 6: 450000},
                ),
                (
                    "other",
                    {1: 75000, 2: 150000, 3: 225000, 4: 300000, 5: 375000, 6: 450000},
                ),
            ]
        )

        new_dict = {}
        for road_type, lanedicts in lookup_dict.items():
            new_lanedict = {}
            for lane, costs in lanedicts.items():
                new_lanedict[lane] = costs / 1000
            new_dict[road_type] = new_lanedict

        lookup_dict = new_dict

        return lookup_dict

    @staticmethod
    def get_flood_curves() -> dict:
        """Lookup flood curve values and create interpolator around it

        Units of the interpolator objects: water depth in cm on x-axis; damage fraction (unitless) on y-axis
        """
        _depth_cm_str = "depth (cm)"
        _damage_str = "damage (% of total construction costs)"
        lookup_dict = {
            "C1": {
                0: _depth_cm_str,
                1: 0,
                2: 50,
                3: 100,
                4: 150,
                5: 200,
                6: 600,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "Unnamed: 2": {
                0: _damage_str,
                1: 0,
                2: 0.01,
                3: 0.03,
                4: 0.075,
                5: 0.1,
                6: 0.2,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "C2": {
                0: _depth_cm_str,
                1: 0,
                2: 50,
                3: 100,
                4: 150,
                5: 200,
                6: 600,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "Unnamed: 4": {
                0: _damage_str,
                1: 0,
                2: 0.02,
                3: 0.06,
                4: 0.1,
                5: 0.12,
                6: 0.22,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "C3": {
                0: _depth_cm_str,
                1: 0,
                2: 50,
                3: 100,
                4: 150,
                5: 200,
                6: 600,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "Unnamed: 6": {
                0: _damage_str,
                1: 0,
                2: 0.002,
                3: 0.004,
                4: 0.025,
                5: 0.03,
                6: 0.04,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "C4": {
                0: _depth_cm_str,
                1: 0,
                2: 50,
                3: 100,
                4: 150,
                5: 200,
                6: 600,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "Unnamed: 8": {
                0: _damage_str,
                1: 0,
                2: 0.015,
                3: 0.04,
                4: 0.2,
                5: 0.25,
                6: 0.35,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "C5": {
                0: _depth_cm_str,
                1: 0,
                2: 50,
                3: 100,
                4: 200,
                5: 600,
                6: np.nan,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "Unnamed: 10": {
                0: _damage_str,
                1: 0,
                2: 0.015,
                3: 0.025,
                4: 0.035,
                5: 0.05,
                6: np.nan,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "C6": {
                0: _depth_cm_str,
                1: 0,
                2: 50,
                3: 100,
                4: 200,
                5: 600,
                6: np.nan,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "Unnamed: 12": {
                0: _damage_str,
                1: 0,
                2: 0.12,
                3: 0.2,
                4: 0.28,
                5: 0.35,
                6: np.nan,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            },
            "HZ": {
                0: _depth_cm_str,
                1: 0.0,
                2: 50.0,
                3: 100.0,
                4: 150.0,
                5: 200.0,
                6: 300.0,
                7: 400.0,
                8: 500.0,
                9: 600.0,
            },
            "Unnamed: 14": {
                0: _damage_str,
                1: 0.0,
                2: 0.25,
                3: 0.42,
                4: 0.55,
                5: 0.65,
                6: 0.8,
                7: 0.9,
                8: 1.0,
                9: 1.0,
            },
        }

        flood_curves = pd.DataFrame.from_dict(lookup_dict)
        headers = flood_curves.columns

        # Convert to ra2ce standard units (depth (m))
        depth_cols = [
            col for col in flood_curves.columns if not col.startswith("Unnamed")
        ]
        flood_curves.loc[1:, depth_cols] = flood_curves.loc[1:, depth_cols] / 100
        flood_curves.loc[0, depth_cols] = "depth (m)"

        curve_name = [0] * int(len(headers) / 2)  # create empty arrays
        interpolators = [0] * int(len(headers) / 2)

        for i in range(0, int(len(headers) / 2)):  # iterate over the damage curves
            curve_name[i] = headers[i * 2]
            curve = flood_curves.iloc[:, 2 * i : 2 * i + 2].dropna()
            # curve x-values in the even; and y-values in the uneven columns
            interpolators[i] = interp1d(
                curve.values[1:, 0],
                curve.values[1:, 1],
                fill_value=(curve.values[1, 1], curve.values[-1, 1]),
                bounds_error=False,
            )
        return OrderedDict(zip(curve_name, interpolators))


class CreateLookupTables:
    """This class lets you create the dictionary lookup tables from an excel file.
    ONLY use this class if dictionairies need to be updated."""

    def __init__(self, settings_file: Path):
        self.settings_file = settings_file

    def create(self):
        lane_damage_correction = self.load_lane_damage_correction("Max_damages", "G:M")
        dict_max_damages = self.import_damage("Max_damages", usecols="C:E")
        max_damages_hz = self.load_hz_max_dam("Huizinga_max_dam", "A:G")
        interpolators = self.import_flood_curves(sheet_name="All_curves", usecols="B:O")

        return (
            lane_damage_correction,
            dict_max_damages,
            max_damages_hz,
            interpolators,
        )

    def load_hz_max_dam(self, sheet_name, usecols):
        """
        Loads the maximum damages according to Huizinga from an Excel file

        Argument:
            *filename* (string) - name of the Excel file (should be located in the input_path dir)
            *sheet_name* (string) - name of the excel sheet name
            *usecols* (string) - the columns which have the data (first column should have the road_type keys)

        Returns:
            *HZ_max_dam* (OrderedDict) - keys are road_types; values are dicts with key: lane, value = correction factor
                Use like: lane_corr['motorway'][4] -> 1.25 (i.e. correct max damage by +25%)
        """

        lane_corr_df = pd.read_excel(
            self.settings_file,
            sheet_name=sheet_name,
            header=0,
            usecols=usecols,
            index_col=0,
        )
        odf = OrderedDict()  # initialize OrderedDict
        hz_max_dam = lane_corr_df.to_dict(orient="index", into=odf)
        return hz_max_dam

    def import_damage(self, sheet_name, usecols):
        """
        Imports the maximum damage data from an Excel file in the input_path folder

        Arguments:
            *file_name* (string) : name of the Excel file (should be located in the input_path folder)
            *sheet_name* (string) : name of the Excel sheet containing the data
            *usecols* (string) : columns containing the data you want to read, including the column with the road_types e.g. "C:F"

        Returns:
            *dict* (Ordered Dictionary) : An ordered dictionary with a group of damage estimates as keys;
                 each value contains another ordered dictionary with as keys the types of roads and as values the damages in Euros
                    So you call the output as: dict['Worldbank'] to get a dict with all the damages in WorldBank
                    And dict['Worldbank']['motorway'] to get the damage for a motorway according to the worldbank

                    #From version 0.7 and higher, this structure maybe does not make much sense, because we use upper and lower bounds

        """

        df = pd.read_excel(
            self.settings_file,
            sheet_name=sheet_name,
            header=[3],
            usecols=usecols,
            index_col=0,
        )
        df = df.iloc[df.index.notna(), :]  # Drop the empty cells
        odf = OrderedDict()  # initialize OrderedDict
        return df.to_dict(into=odf)

    def load_lane_damage_correction(self, sheet_name, usecols):
        """
        Loads the maximum damage correction from an Excel file into an ordered dict.

        Argument:
            *filename* (string) - name of the Excel file (should be located in the input_path dir)
            *sheet_name* (string) - name of the excel sheet name
            *usecols* (string) - the columns which have the data (first column should have the road_type keys)

        Returns:
            *lane_corr* (OrderedDict) - keys are road_types; values are dicts with key: lane, value = correction factor
                Use like: lane_corr['motorway'][4] -> 1.25 (i.e. correct max damage by +25%)
        """

        lane_corr_df = pd.read_excel(
            self.settings_file,
            sheet_name=sheet_name,
            header=3,
            usecols=usecols,
            index_col=0,
        )
        odf = OrderedDict()  # initialize OrderedDict
        lane_corr = lane_corr_df.to_dict(orient="index", into=odf)
        return lane_corr

    def import_flood_curves(self, sheet_name, usecols):
        """
        Imports the flood curves from a predefined path

        Arguments:
            *filename* (string) : name of the Excel file (should be located in the input_path folder) e.g. "Costs_curves_Europe.xlsx"
            *sheet_name* (string) : name of the Excel sheet containing the damage curves (e.g. 'curves')
            *usecols* (string) : string with the columns of the Excel sheet you want to import, e.g. "B:AA"

        Returns:
            *OrderedDict* : keys are the names of the damage curves
                            values are scipy interpolators
        """

        flood_curves_old = pd.read_excel(
            self.settings_file,
            sheet_name=sheet_name,
            header=[2],
            index_col=None,
            usecols=usecols,
        )  # removed skip-footer; gave unexpected results
        flood_new = flood_curves_old.to_dict()
        flood_curves = pd.DataFrame.from_dict(flood_new)

        headers = flood_curves.columns
        curve_name = [0] * int(len(headers) / 2)  # create empty arrays
        interpolators = [0] * int(len(headers) / 2)
        for i in range(
            0, int(len(headers) / 2)
        ):  # iterate over the damage curves in the Excel file
            curve_name[i] = headers[i * 2]
            curve = flood_curves.iloc[:, 2 * i : 2 * i + 2].dropna()
            # curve x-values in the even; and y-values in the uneven columns
            interpolators[i] = interp1d(
                curve.values[1:, 0],
                curve.values[1:, 1],
                fill_value=(curve.values[1, 1], curve.values[-1, 1]),
                bounds_error=False,
            )
        return OrderedDict(zip(curve_name, interpolators))
