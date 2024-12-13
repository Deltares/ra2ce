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
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame
from scipy.interpolate import interp1d

from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.damages.damage_functions.manual_damage_functions import (
    ManualDamageFunctions,
)
from ra2ce.analysis.damages.damages_lookup import LookUp as lookup
from ra2ce.analysis.damages.damages_lookup import dataframe_lookup
from ra2ce.analysis.damages.damages_utils import (
    clean_lane_data,
    create_summary_statistics,
    scale_damage_using_lanes,
)


class DamageNetworkBase(ABC):
    """A road network gdf with hazard data stored in it, and for which damages can be calculated"""

    def __init__(
        self,
        road_gdf: GeoDataFrame,
        val_cols: list[str],
        representative_damage_percentage: float,
    ):
        """Construct the Data"""
        self.val_cols = val_cols
        self.gdf = road_gdf
        # set of hazard info per event
        self.stats = set([x.split("_")[-1] for x in val_cols])
        self.representative_damage_percentage = representative_damage_percentage
        # TODO: also track the damage cols after the dam calculation, that is useful for the risk calc. module
        # TODO: also create constructors of the children of this class

    @abstractmethod
    def main(
        self,
        damage_function: DamageCurveEnum,
        manual_damage_functions: ManualDamageFunctions,
    ):
        """
        Controller for doing the EAD calculation

        Args:
            damage_function (DamageCurveEnum): damage function key name that is to be used
            manual_damage_functions (ManualDamageFunctions): `ManualDamageFunctions` object
        """
        raise ValueError("Needs to be implemented in concrete child class.")

    # events is missing
    def do_cleanup_and_mask_creation(self):
        """Call all cleanup and mask functions, because this is a standard procedure in most calculations"""
        # CLEANUPS (on the original gdf)
        self.remap_road_types_to_fewer_classes()
        self.clean_and_interpolate_missing_lane_data()
        self.fix_extraordinary_lanes()

        # Mask creation
        self.create_mask()
        self.remove_unclassified_road_types_from_mask()

    ### Generic cleanup functionality
    def fix_extraordinary_lanes(self):
        """Remove exceptionally high/low lane numbers in self.gdf"""
        # fixing lanes
        df = self.gdf
        df["lanes_copy"] = df["lanes"].copy()
        df["lanes"] = df["lanes_copy"].where(
            df["lanes_copy"].astype(float) >= 1.0, other=1.0
        )
        df["lanes"] = df["lanes_copy"].where(
            df["lanes_copy"].astype(float) <= 6.0, other=6.0
        )
        df = self.gdf

    def clean_and_interpolate_missing_lane_data(self):
        # cleanup and complete the lane data.
        ### Try to convert all data to floats
        try:
            self.gdf.lanes = self.gdf.lanes.astype(
                "float"
            )  # floats instead of ints because ints cannot be nan.
        except Exception:
            logging.warning(
                "Available lane data cannot simply be converted to float/int, RA2CE will try a clean-up."
            )
            self.gdf.lanes = clean_lane_data(self.gdf.lanes)

        # round to nearest integer, but save as float format
        self.gdf.lanes = self.gdf.lanes.round(0)

        # boolean with trues for all nans, i.e. all road segements without lane data
        nans = self.gdf.lanes.isnull()
        if nans.sum() > 0:
            logging.warning(
                """Of the {} road segments, only {} had lane data, so for {} the '
                                    lane data will be interpolated from the existing data""".format(
                    len(self.gdf.lanes), (~nans).sum(), nans.sum()
                )
            )
            lane_stats = create_summary_statistics(self.gdf)

            # Replace the missing lane data the neat way (without pandas SettingWithCopyWarning)
            lane_nans_mask = self.gdf.lanes.isnull()
            self.gdf.loc[lane_nans_mask, "lanes"] = self.gdf.loc[
                lane_nans_mask, "road_type"
            ].replace(lane_stats)
            logging.warning(
                "Interpolated the missing lane data as follows: {}".format(lane_stats)
            )
            # all nans should be replaced
            assert np.nan not in self.gdf.lanes.unique()

        # TODO: think about if this is the best option
        self.gdf.loc[self.gdf["lanes"] == 0, "lanes"] = 1

    def remap_road_types_to_fewer_classes(self):
        """
        Creates a new new column road_types, which has a fewer number of road type categories
        e.g. -> 'motorway_junction' -> 'motorway'
        (Renames highway column to infra_type)
        :return:
        """
        # reduce the number of road types (col 'infra_type') to smaller number of road_types for which damage curves exist
        road_mapping_dict = (
            lookup.road_mapping()
        )  # The lookup class contains all kinds of data
        gdf = self.gdf
        gdf.rename(
            columns={"highway": "infra_type"}, inplace=True
        )  # Todo: this should probably not be done here
        gdf["road_type"] = gdf["infra_type"]
        gdf = gdf.replace({"road_type": road_mapping_dict})
        self.gdf = gdf

    def remove_unclassified_road_types_from_mask(self):
        """
        Drop all rows with road types classified as 'none' from the self._gdf_mask

        :return:
        """
        df = self._gdf_mask
        if "none" in df["road_type"].unique():
            to_drop = df.loc[df["road_type"] == "none"]
            logging.warning(
                "We will drop {} rows for which the road_type is unrecognized".format(
                    to_drop.shape[0]
                )
            )
            self._gdf_mask = df.loc[~(df["road_type"] == "none")]

    ### Damage handlers
    def calculate_damage_manual_functions(
        self, events: list[str], manual_damage_functions: ManualDamageFunctions
    ) -> None:
        """
        Calculate the damage using the manual damage functions

        Args:
            events (list[str]): list of events (or return periods) to iterate over, these should match the hazard column names
            manual_damage_functions (ManualDamageFunctions): The manual damage functions object
        """
        # Todo: Dirty fixes, these should be read from the init
        hazard_prefix = "F"

        # dataframe to carry out the damage calculation #todo: this is a bit dirty
        df = self._gdf_mask

        assert (
            len(manual_damage_functions.damage_functions) > 0
        ), "No damage functions were loaded"

        for _damage_func in manual_damage_functions.damage_functions.values():
            # Add max damage values to df
            df = _damage_func.add_max_damage(df, _damage_func.prefix)
            for event in events:
                # Add apply interpolator objects
                event_prefix = event
                df = _damage_func.calculate_damage(
                    df, _damage_func.prefix, hazard_prefix, event_prefix
                )

        # Only transfer the final results to the damage column
        dam_cols = [c for c in df.columns if c.startswith("dam_")]
        self.gdf[dam_cols] = df[dam_cols]
        logging.info(
            "Damage calculation with the manual damage functions was succesfull."
        )

    def calculate_damage_HZ(self, events: list[str]) -> None:
        """
        Arguments:
           *events* (list) = list of events (or return periods) to iterate over, these should match the hazard column names
        """
        # These factors are derived from: Van Ginkel et al. 2021: https://nhess.copernicus.org/articles/21/1011/2021/
        logging.warning(
            "Damage calculations with Huizinga curves are based on Van Ginkel et al. 2021: https://nhess.copernicus.org/articles/21/1011/2021/"
        )
        logging.warning(
            """All damages represent the former EU-28 (before Brexit), 2015-pricelevel in Euro's.
                            To convert to local currency, these need to be:
                                multiplied by the ratio (pricelevel_XXXX / pricelevel_2015)
                                multiply by the ratio (local_GDP_per_capita / EU-28-2015-GDP_per_capita)          
                            EU-28-2015-GDP_per_capita = 39.200 euro
                        """
        )
        logging.warning(
            "These numbers assume that motorways that each driving direction is mapped as a seperate segment such as in OSM!!!"
        )

        # Todo: Dirty fixes, these should be read from the init
        hazard_prefix = "F"
        end = "me"  # indicate that you want to use the mean

        # Load the Huizinga damage functions
        curve_name = "HZ"

        df_max_damages_huizinga = pd.DataFrame.from_dict(
            lookup.get_max_damages_huizinga()
        )
        interpolator = lookup.get_flood_curves()[
            "HZ"
        ]  # input: water depth (cm); output: damage (fraction road construction costs)

        df = self._gdf_mask
        df["lanes"] = df["lanes"].astype(int)
        df["max_dam_hz"] = df.apply(
            dataframe_lookup,
            args=(df_max_damages_huizinga, ["lanes", "road_type"]),
            axis=1,
        )

        for event in events:
            df["dam_{}_{}".format(event, curve_name)] = round(
                df["max_dam_hz"].astype(float)  # max damage (euro/m)
                * interpolator(df["{}_{}_{}".format(hazard_prefix, event, end)]).astype(
                    float
                )  # damage curve  (-)
                * df["{}_{}_{}".format(hazard_prefix, event, "fr")].astype(
                    float
                )  # inundated fraction (-)
                * df["length"],
                2,
            )  # length segment (m)

        # Add the new columns add the right location to the df
        dam_cols = [c for c in df.columns if c.startswith("dam_")]

        self.gdf[dam_cols] = df[dam_cols]
        logging.info(
            "calculate_damage_HZ(): Damage calculation with the Huizinga damage functions was successful"
        )

    def calculate_damage_OSdaMage(self, events: list[str]) -> None:
        """Damage calculation with the OSdaMage functions"""

        def interpolate_damage(row, representative_damage_percentage):
            # Extract the tuple of damage values from the row
            damage_values = row["dam_{}_{}_quartiles".format(curve_name, event)]

            # Quantile values corresponding to the damage values
            percentages = [0, 25, 50, 75, 100]

            # Perform linear interpolation using interp1d from scipy
            _interpolator = interp1d(
                percentages, damage_values, kind="linear", fill_value="extrapolate"
            )

            # Interpolate the damage value for the given representative_damage_percentage
            interpolated_damage = _interpolator(representative_damage_percentage)

            return interpolated_damage

        # These factors are derived from: Van Ginkel et al. 2021: https://nhess.copernicus.org/articles/21/1011/2021/
        logging.warning(
            """Damage calculations with OSdaMage functions are based on 
            Van Ginkel et al. 2021: https://nhess.copernicus.org/articles/21/1011/2021/"""
        )
        logging.warning(
            """All damages represent the former EU-28 (before Brexit), 2015-pricelevel in Euro's.
                            To convert to local currency, these need to be:
                                multiplied by the ratio (pricelevel_XXXX / pricelevel_2015)
                                multiply by the ratio (local_GDP_per_capita / EU-28-2015-GDP_per_capita)          
                            EU-28-2015-GDP_per_capita = 39.200 euro
                        """
        )
        logging.warning(
            "These numbers assume that motorways that each driving direction is mapped as a seperate segment such as in OSM!!!"
        )

        # Todo: Dirty fixes, these should be read from the configuration file
        hazard_prefix = "F"
        end = "me"  # indicate that you want to use the mean

        # Load the OSdaMage functions
        max_damages = lookup.get_max_damages_osd()
        interpolators = lookup.get_flood_curves()
        interpolators.pop(
            "HZ"
        )  # input: water depth (cm); output: damage (fraction road construction costs)
        lane_scale_factors = lookup.get_lane_number_damage_correction()

        # Prepare the output files
        df = self._gdf_mask
        df["tuple"] = [tuple([0] * 5)] * len(df["lanes"])

        # CALCULATE MINIMUM AND MAXIMUM CONSTRUCTION COST PER ROAD TYPE
        # pre-calculation of max damages per percentage (same for each C1-C6 category)
        df["lower_damage"] = (
            df["road_type"].copy().map(max_damages["Lower"])
        )  # i.e. min construction costs
        df["upper_damage"] = (
            df["road_type"].copy().map(max_damages["Upper"])
        )  # i.e. max construction costs

        # apply damage correction for lanes
        cols_to_scale = ["lower_damage", "upper_damage"]
        df = scale_damage_using_lanes(lane_scale_factors, df, cols_to_scale)

        # create separate column for each percentage of construction costs (is faster then tuple)
        for percentage in [
            0,
            25,
            50,
            75,
            100,
        ]:  # So this interpolates the min to the max damage
            df["damage_{}".format(percentage)] = (
                df["upper_damage"] * percentage / 100
            ) + (df["lower_damage"] * (100 - percentage) / 100)

        for curve_name, interpolator in interpolators.items():
            # print(curve_name, interpolator)
            for event in events:
                for percentage in [0, 25, 50, 75, 100]:
                    df["dam_{}_{}_{}".format(percentage, curve_name, event)] = round(
                        df["damage_{}".format(percentage)].astype(
                            float
                        )  # max damage (in euro/m)
                        * interpolator(
                            df["{}_{}_{}".format(hazard_prefix, event, end)]
                        ).astype(
                            float
                        )  # damage curve: fraction f(depth-cm) #Todo check units
                        * df["{}_{}_{}".format(hazard_prefix, event, "fr")].astype(
                            float
                        )  # inundated fraction of the segment should be in km. because max damage (in euro/km)
                        * df["length"].astype(float),
                        3,
                    )

                # This wraps it all in tuple again
                df["dam_{}_{}_quartiles".format(curve_name, event)] = tuple(
                    zip(
                        df["dam_0_{}_{}".format(curve_name, event)],
                        df["dam_25_{}_{}".format(curve_name, event)],
                        df["dam_50_{}_{}".format(curve_name, event)],
                        df["dam_75_{}_{}".format(curve_name, event)],
                        df["dam_100_{}_{}".format(curve_name, event)],
                    )
                )
                df[f"dam_{curve_name}_{event}_representative"] = (
                    df.apply(
                        lambda row: interpolate_damage(
                            row, self.representative_damage_percentage
                        ),
                        axis=1,
                    )
                ).astype(float)

                # And throw way all intermediate results (that are not in the tuple)
                df = df.drop(
                    columns=[
                        "dam_{}_{}_{}".format(percentage, curve_name, event)
                        for percentage in [0, 25, 50, 75, 100]
                    ]
                )

        df = df.drop(columns=[c for c in df.columns if c.startswith("damage_")])

        # drop invalid combinations of damage curves and road types (C1-C4 for motorways; C5,C6 for other)
        all_dam_cols = [c for c in df.columns if c.startswith("dam_")]
        motorway_curves = [
            c for c in all_dam_cols if int(c.split("_")[1][-1]) <= 4
        ]  # C1-C4
        other_curves = [
            c for c in all_dam_cols if int(c.split("_")[1][-1]) > 4
        ]  # C5, C6

        is_motorway_mask = df["road_type"].isin(["motorway", "trunk"])

        for curve in other_curves:
            df.loc[is_motorway_mask, curve] = np.nan

        for curve in motorway_curves:
            df.loc[~is_motorway_mask, curve] = np.nan

        # Add the new columns add the right location to the df
        self.gdf[all_dam_cols] = df[all_dam_cols]
        logging.info(
            "calculate_damage_OSdaMage(): Damage calculation with the OSdaMage functions was succesfull"
        )

    ### Utils handlers
    def create_mask(self) -> None:
        """
        #Create a mask of only the dataframes with hazard data (to speed-up damage calculations)
        effect: *self._gdf_mask* = mask of only the rows with hazard data

        """

        # because the fractions are often 0 (also if the rest is nan, this messes up the .isna)
        val_cols_temp = [c for c in self.val_cols if "_fr" not in c]
        gdf_mask = self.gdf.loc[~(self.gdf[val_cols_temp].isna()).all(axis=1)]
        self._gdf_mask = gdf_mask  # todo: not sure if we need to store the mask

        # Also remove the geometries from the mask
        column_names = list(self._gdf_mask.columns)
        if "geometry" in column_names:
            column_names.remove("geometry")
        self._gdf_mask = self._gdf_mask[column_names]

    def replace_none_with_nan(self) -> None:
        dam_cols = [c for c in self.gdf.columns if c.startswith("dam_")]
        self.gdf[dam_cols] = self.gdf[dam_cols].fillna(value=np.nan)
