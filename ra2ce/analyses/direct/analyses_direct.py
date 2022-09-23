# -*- coding: utf-8 -*-
"""
@authors: Kees van Ginkel, Bramka Jafino, Frederique de Groen, Martijn Kwant, Elco Koks
Created on 26-7-2021
"""

import logging
import os
import sys
import time

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from ra2ce.analyses.direct.direct_lookup import LookUp as lookup
from ra2ce.analyses.direct.direct_utils import *

folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder)


class DirectAnalyses:  ### THIS SHOULD ONLY DO COORDINATION
    def __init__(self, config, graphs):
        self.config = config
        self.graphs = graphs

    def execute(self):
        """Main Coordinator of all direct damage analysis"""
        for analysis in self.config['direct']:
            logging.info(f"----------------------------- Started analyzing '{analysis['name']}'  -----------------------------")
            starttime = time.time()

            if analysis['analysis'] == 'direct':

                gdf = self.road_damage(analysis) #calls the coordinator for road damage calculation

            elif analysis['analysis'] == 'effectiveness_measures':
                gdf = self.effectiveness_measures(analysis)

            else:
                gdf = []

            output_path = self.config['output'] / analysis['analysis']
            if analysis['save_shp']:
                shp_path = output_path / (analysis['name'].replace(' ', '_') + '.shp')
                save_gdf(gdf, shp_path)
            if analysis['save_csv']:
                csv_path = output_path / (analysis['name'].replace(' ', '_') + '.csv')
                del gdf['geometry']
                gdf.to_csv(csv_path, index=False)

            endtime = time.time()
            logging.info(f"----------------------------- Analysis '{analysis['name']}' finished. "
                         f"Time: {str(round(endtime - starttime, 2))}s  -----------------------------")

    def road_damage(self, analysis):
        """
        ### CONTROLER FOR CALCULATING THE ROAD DAMAGE

        Arguments:
            *analysis* (dict) : contains part of the settings from the analysis ini
        :return:
        """
        #Open the network with hazard data
        road_gdf = self.graphs["base_network_hazard"]
        if self.graphs["base_network_hazard"] is None:
            road_gdf = gpd.read_feather(self.config["files"]["base_network_hazard"])

        # Find the hazard columns #Todo: use the hazard names .xlsx?
        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        # Read the desired damage function
        damage_function = analysis['damage_curve']

        #If you want to use manual damage functions, the need to be loaded first
        manual_damage_functions = None
        if analysis['damage_curve'] == 'MAN':
            manual_damage_functions = ManualDamageFunctions()
            manual_damage_functions.find_damage_functions(folder=(self.config['input'] / 'damage_functions'))
            manual_damage_functions.load_damage_functions()

        #Choose between event or return period based analysis
        if analysis['event_type'] == 'event':
            event_cols = [x for x in val_cols if "_EV" in x] #Todo: can be part of the init of the object

            if not len(event_cols) > 0:
                raise ValueError('No event cols present in hazard data')

            event_gdf = DamageNetworkEvents(road_gdf, val_cols)
            event_gdf.main(damage_function=damage_function,manual_damage_functions=manual_damage_functions)

            result_gdf = event_gdf.gdf

            return result_gdf

        elif analysis['event_type'] == 'return_period':
            #count number of return period cols
            rp_cols = [x for x in val_cols if "_RP" in x] #Todo: can be part of the init of the object

            if not len(rp_cols) > 1: #Todo, can be done after, or in object instantiation
                raise ValueError('No return_period cols present in hazard data')

            #return_period_gdf.main(damage_function=damage_function) #DEPRECATED
            return_period_gdf = DamageNetworkReturnPeriods(road_gdf,val_cols)
            DamageNetworkReturnPeriods.main(damage_function=damage_function)

            result_gdf = return_period_gdf.gdf

            return result_gdf

        else:
            raise ValueError(
                """"The hazard calculation does not know 
            what to do if the analysis specifies {}""".format(
                    analysis['event_type']
                )
            )


        # # TODO I, Kees think this is a dangerous cleanup procedure with possible unexpected outcomes
        # # cleanup of gdf
        # for column in gdf.columns:
        #     gdf[column] = gdf[column].apply(
        #         rd.apply_cleanup
        #     )  # Todo: rename function, this is too vague.

        # calculate direct damage
        #road_gdf_damage = rd.calculate_direct_damage(gdf)



    def effectiveness_measures(self, analysis):
        """This function calculated the efficiency of measures. Input is a csv file with efficiency
        and a list of different aspects you want to check.
        """
        em = EffectivenessMeasures(self.config, analysis)
        effectiveness_dict = em.load_effectiveness_table(
            self.config["input"] / "direct"
        )

        if self.graphs["base_network_hazard"] is None:
            gdf_in = gpd.read_feather(self.config["files"]["base_network_hazard"])

        if analysis["create_table"] is True:
            df = em.create_feature_table(
                self.config["input"] / "direct" / analysis["file_name"]
            )
        else:
            df = em.load_table(
                self.config["input"] / "direct",
                analysis["file_name"].replace(".shp", ".csv"),
            )

        df = em.calculate_strategy_effectiveness(df, effectiveness_dict)
        df = em.knmi_correction(df)
        df_cba, costs_dict = em.cost_benefit_analysis(effectiveness_dict)
        df_cba.round(2).to_csv(
            self.config["output"] / analysis["analysis"] / "cost_benefit_analysis.csv",
            decimal=",",
            sep=";",
            index=False,
            float_format="%.2f",
        )
        df = em.calculate_cost_reduction(df, effectiveness_dict)
        df_costs = em.calculate_strategy_costs(df, costs_dict)
        df_costs = df_costs.astype(float).round(2)
        df_costs.to_csv(
            self.config["output"] / analysis["analysis"] / "output_analysis.csv",
            decimal=",",
            sep=";",
            index=False,
            float_format="%.2f",
        )
        gdf = gdf_in.merge(df, how="left", on="LinkNr")
        return gdf


#Todo: old functions of the deprecated class
# def apply_lane_damage_correction(lane_damage_correction, road_type, lanes):
#         """See load_lane_damage_correction; this function only avoids malbehaviour for weird lane numbers"""
#         if lanes < 1:  # if smaller than the mapped value -> correct with minimum value
#             lanes = 1
#         if (
#             lanes > 6
#         ):  # if larger than largest mapped value -> use maximum value (i.e. 6 lanes)
#             lanes = 6
#         return lane_damage_correction[road_type][lanes]
#
#
# def apply_huizinga_max_dam(max_damages_huizinga, road_type, lanes):
#         """See load_lane_damage_correction; this function only avoids malbehaviour for weird lane numbers"""
#         if lanes < 1:  # if smaller than the mapped value -> correct with minimum value
#             lanes = 1
#         if (
#             lanes > 6
#         ):  # if larger than largest mapped value -> use maximum value (i.e. 6 lanes)
#             lanes = 6
#         return max_damages_huizinga[road_type][lanes]
#
#
# def apply_cleanup(x):
#         """Cleanup for entries in dataframe, where there is a list with two values for a single field.
#
#         This happens when there is both a primary_link and a primary infra_type.
#         x[0] indicates the values of the primary_link infra_type
#         x[1] indicates the values of the primary infra_type
#         """
#         if x is None:
#             return None
#         if type(x) == list:
#             return x[1]  # 1 means select primary infra_type
#         else:
#             return x


def save_gdf(gdf, save_path):
    """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

    Arguments:
        gdf [geodataframe]: geodataframe object to be converted
        edge_shp [str]: output path including extension for edges shapefile
        node_shp [str]: output path including extension for nodes shapefile
    Returns:
        None
    """
    # save to shapefile
    gdf.crs = "epsg:4326"  # TODO: decide if this should be variable with e.g. an output_crs configured

    for col in gdf.columns:
        if gdf[col].dtype == object and col != gdf.geometry.name:
            gdf[col] = gdf[col].astype(str)

    gdf.to_file(save_path, driver="ESRI Shapefile", encoding="utf-8")
    logging.info("Results saved to: {}".format(save_path))


# DATA STRUCTURES
# Todo: make a general class from which these two datatypes inherit.
class rp_hazard_network_gdf_standalone: #DEPRECIATED, SEE BELOW
    """A road network gdf with hazard data per return period stored in it. This can be used for EAD calculation

    @Author: Kees van Ginkel, - I made this as an example of how we could develop the code more object-based

    Mandatory attributes:
        *self.rps* (set)  : all available unique events
        *self.stats* (set)   : the available statistics
    """

    # Todo check how you can built this on top of geopandas df
    def __init__(self, road_gdf, val_cols):
        """Construct the network gdf and make some handy attributes

        Arguments:
            *road_gdf* (GeoPandas Dataframe) : the results from the hazard overlay module
            *val_cols* (list) : name of the columns that contain the return period data
        """
        # todo self.hazard name
        self.val_cols = val_cols
        self.rps = set(
            [x.split("_")[1] for x in val_cols]
        )  # set of unique return periods
        self.stats = set(
            [x.split("_")[2] for x in val_cols]
        )  # set of availabe hazard info per event
        self.gdf = road_gdf


# DATA STRUCTURES
class DamageNetwork:
    """A road network gdf with hazard data stored in it, and for which damages can be calculated"""

    def __init__(self, road_gdf, val_cols):
        """Construct the Data"""
        self.val_cols = val_cols
        self.gdf = road_gdf
        self.stats = set(
            [x.split("_")[2] for x in val_cols]
        )  # set of hazard info per event
        # events is missing

    ### Controlers
    def identify_hazard_type(self):  # This is a controler, which should not be here.
        pass

    ### Generic cleanup functionality
    def fix_extraordinary_lanes(self):
        """Remove exceptionally high/low lane numbers """
        # fixing lanes
        df = self.df
        df["lanes_copy"] = df["lanes"].copy()
        df["lanes"] = df["lanes_copy"].where(
            df["lanes_copy"].astype(float) >= 1.0, other=1.0
        )
        df["lanes"] = df["lanes_copy"].where(
            df["lanes_copy"].astype(float) <= 6.0, other=6.0
        )
        df = self.df

    def clean_and_interpolate_missing_lane_data(self):
        # cleanup and complete the lane data.
        ### Try to convert all data to floats
        gdf = self.gdf
        try:
            gdf.lanes = gdf.lanes.astype('float')  # floats instead of ints because ints cannot be nan.
        except:
            logging.warning('Available lane data cannot simply be converted to float/int, RA2CE will try a clean-up.')
            gdf.lanes = clean_lane_data(gdf.lanes)

        gdf.lanes = gdf.lanes.round(0)  # round to nearest integer, but save as float format
        nans = gdf.lanes.isnull()  # boolean with trues for all nans, i.e. all road segements without lane data
        if nans.sum() > 0:
            logging.warning("""Of the {} road segments, only {} had lane data, so for {} the '
                                    lane data will be interpolated from the existing data""".format(
                len(gdf.lanes), (~nans).sum(), nans.sum()))
            lane_stats = create_summary_statistics(gdf)

            # Replace the missing lane data the neat way (without pandas SettingWithCopyWarning)
            lane_nans_mask = gdf.lanes.isnull()
            gdf.loc[lane_nans_mask, 'lanes'] = gdf.loc[lane_nans_mask, 'road_type'].replace(lane_stats)
            logging.warning('Interpolated the missing lane data as follows: {}'.format(lane_stats))

            # Todo: write the whole interpolater object

            # This worked but raises an error
            # lane_nans = gdf[gdf.lanes.isnull()]  # mask all nans in lane data
            # lane_nans['lanes'] =  lane_nans['road_type'].replace(lane_stats)
            # gdf.loc[lane_nans.index, :] = lane_nans

            # Todo: What if for one road type all lane data is missing?
            # Todo: we could script a seperate work-around for this situation, for now we just raise an assertion
            assert not (np.nan in gdf.lanes.unique())  # all nans should be replaced

        gdf.loc[gdf['lanes'] == 0, 'lanes'] = 1  #TODO: think about if this is the best option

        self.gdf = gdf

    def remap_road_types_to_fewer_classes(self):
        """
        Creates a new new column road_types, which has a fewer number of road type categories
        e.g. -> 'motorway_junction' -> 'motorway'
        (Renames highway column to infra_type)
        :return:
        """
        # reduce the number of road types (col 'infra_type') to smaller number of road_types for which damage curves exist
        road_mapping_dict = lookup.road_mapping()  # The lookup class contains all kinds of data
        gdf = self.gdf
        gdf.rename(columns={'highway': 'infra_type'}, inplace=True) #Todo: this should probably not be done here
        gdf['road_type'] = gdf['infra_type']
        gdf = gdf.replace({"road_type": road_mapping_dict})
        self.gdf = gdf


    ### Damage handlers
    def calculate_damage_manual_functions(self,events,manual_damage_functions):
        """
        Arguments:
        *events* (list) = list of events (or return periods) to iterate over, these should match the hazard column names 
        """

        # Todo: Dirty fixes, these should be read from the init
        hazard_prefix = "F"
        end = "me"  # indicate that you want to use the mean

        df = self.df #dataframe to carry out the damage calculation #todo: this is a bit dirty

        assert manual_damage_functions is not None, "No damage functions were loaded"

        for DamFun in manual_damage_functions.loaded:
            #Add max damage values to df
            df = DamFun.add_max_damage(df,DamFun.prefix)
            for event in events:
                #Add apply interpolator objects
                event_prefix = event
                df = DamFun.calculate_damage(df,DamFun.prefix,hazard_prefix,event_prefix)

        #Only transfer the final results to the damage column
        dam_cols = [c for c in df.columns if c.startswith("dam_")]
        self.gdf[dam_cols] = df[dam_cols]
        logging.info(
            "Damage calculation with the manual damage functions was succesfull."
        )


    def calculate_damage_HZ(self, events):
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

        df_max_damages_huizinga = pd.DataFrame.from_dict(lookup.max_damages_huizinga())
        #max_damages_huizinga = lookup.max_damages_huizinga()
        interpolator = lookup.flood_curves()[
            "HZ"
        ]  # input: water depth (cm); output: damage (fraction road construction costs)

        df = self.df
        df["lanes"] = df["lanes"].astype(int)
        df["max_dam_hz"] = df_max_damages_huizinga.lookup(df["lanes"], df["road_type"])

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

        # Todo: still need to check the units
        #logging.warning("The units for the damage calculation have been corrected, but the inundated fraction not")

        # Add the new columns add the right location to the df
        dam_cols = [c for c in df.columns if c.startswith("dam_")]
        self.gdf[dam_cols] = df[dam_cols]
        logging.info(
            "calculate_damage_HZ(): Damage calculation with the Huizinga damage functions was succesfull"
        )

    def calculate_damage_OSdaMage(self, events):
        """OSdaMage calculation not yet implemented"""

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



        # Todo: Dirty fixes, these should be read from the code
        hazard_prefix = "F"
        end = "me"  # indicate that you want to use the mean

        # Load the OSdaMage functions
        max_damages = lookup.max_damages()
        interpolators = lookup.flood_curves()
        interpolators.pop(
            "HZ"
        )  # input: water depth (cm); output: damage (fraction road construction costs)

        # Prepare the output files
        df = self.df
        df["tuple"] = [tuple([0] * 5)] * len(df["lanes"])

        # CALCULATE MINIMUM AND MAXIMUM CONSTRUCTION COST PER ROAD TYPE
        # pre-calculation of max damages per percentage (same for each C1-C6 category)
        df["lower_damage"] = (
            df["road_type"].copy().map(max_damages["Lower"])
        )  # i.e. min construction costs
        df["upper_damage"] = (
            df["road_type"].copy().map(max_damages["Upper"])
        )  # i.e. max construction costs

        # create separate column for each percentile of construction costs (is faster then tuple)
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

        columns = []
        for curve_name, interpolator in interpolators.items():
            # print(curve_name, interpolator)
            for event in events:
                for percentage in [0, 25, 50, 75, 100]:
                    df["dam_{}_{}_{}".format(percentage, curve_name, event)] = round(
                        df["damage_{}".format(percentage)].astype(
                            float
                        )  # max damage (in euro/km)
                        * interpolator(
                            df["{}_{}_{}".format(hazard_prefix, event, end)]
                        ).astype(
                            float
                        )  # damage curve: fraction f(depth-cm) #Todo check units
                        * df["{}_{}_{}".format(hazard_prefix, event, "fr")].astype(
                            float
                        )  # inundated fraction of the segment
                        * df["length"].astype(float),
                        2,
                    )

                # This wraps it all in tuple again
                df["dam_{}_{}".format(curve_name, event)] = tuple(
                    zip(
                        df["dam_0_{}_{}".format(curve_name, event)],
                        df["dam_25_{}_{}".format(curve_name, event)],
                        df["dam_50_{}_{}".format(curve_name, event)],
                        df["dam_75_{}_{}".format(curve_name, event)],
                        df["dam_100_{}_{}".format(curve_name, event)],
                    )
                )

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

        for curve in other_curves:
            df.loc[df["road_type"] == ("motorway" or "trunk"), curve] = np.nan

        for curve in motorway_curves:
            df.loc[df["road_type"] != ("motorway" or "trunk"), curve] = np.nan

        # Todo: still need to check the units
        logging.warning("Damage calculation units have not been checked!!! TODO")

        # Add the new columns add the right location to the df
        self.gdf[all_dam_cols] = df[all_dam_cols]
        logging.info(
            "calculate_damage_OSdaMage(): Damage calculation with the OSdaMage functions was succesfull"
        )

        ### Utils handlers

    def create_mask(self):
        """
        #Create a mask of only the dataframes with hazard data (to speed-up damage calculations)
        effect: *self.gdf_mask* = mask of only the rows with hazard data
        also returns this value
        """
        # because the fractions are often 0 (also if the rest is nan, this messes up the .isna)
        val_cols_temp = [c for c in self.val_cols if "_fr" not in c]

        gdf_mask = self.gdf.loc[~(self.gdf[val_cols_temp].isna()).all(axis=1)]
        self.gdf_mask = gdf_mask  # todo: not sure if we need to store the mask
        return gdf_mask


class DamageNetworkReturnPeriods(DamageNetwork):
    """A road network gdf with Return-Period based hazard data stored in it, and for which damages can be calculated

    @Author: Kees van Ginkel

    Mandatory attributes:
        *self.rps* (set)  : all available unique events
        *self.stats* (set)   : the available statistics
    """

    def __init__(self, road_gdf, val_cols):
        # Construct using the parent class __init__
        DamageNetwork.__init__(self, road_gdf, val_cols)
        self.return_periods = set(
            [x.split("_")[1] for x in val_cols]
        )  # set of unique return_periods

    ### Controlers for EAD calculation
    def main(self, damage_function):
        """Controler for doing the EAD calculation

        Arguments:
            *damage_function* = damage function that is to be used, valid arguments are: 'HZ', 'OSD', 'MAN'

        """

        assert len(self.return_periods) > 0, "no return periods identified"
        assert "me" in self.stats, "mean water depth (key: me) is missing"
        assert "fr" in self.stats, "inundated fraction (key: fr) is missing"


        #CLEANUPS
        self.remap_road_types_to_fewer_classes()
        self.clean_and_interpolate_missing_lane_data()

        gdf_mask = self.create_mask()

        # create dataframe from gdf  #Todo: check why this is necessary
        column_names = list(gdf_mask.columns)
        column_names.remove("geometry")
        df = gdf_mask[column_names]

        self.df = df  # helper dataframe to speedup the analysis
        self.fix_extraordinary_lanes()

        if damage_function == "HZ":
            self.calculate_damage_HZ(events=self.return_periods)

        if damage_function == "OSD":
            self.calculate_damage_OSdaMage(events=self.return_periods)

class DamageNetworkEvents(DamageNetwork):
    """A road network gdf with EVENT-BASED hazard data stored in it, and for which damages can be calculated

    @Author: Kees van Ginkel

    Mandatory attributes:
        *self.events* (set)  : all available unique events
        *self.stats* (set)   : the available statistics
    """

    # Todo for pakistan project, make this working, by taking the code from below
    # Todo: But let's start with the manual damage curves (and take Huizinga as an example)

    def __init__(self, road_gdf, val_cols):
        # Construct using the parent class __init__
        DamageNetwork.__init__(self, road_gdf, val_cols)
        self.events = set(
            [x.split("_")[1] for x in val_cols]
        )  # set of unique events

    ### Controler for Event-based damage calculation
    def main(self, damage_function,manual_damage_functions):
        """Controler for doing the EAD calculation

        Arguments:
            *damage_function* = damage function that is to be used, valid arguments are: 'HZ', 'OSD', 'MAN'

        """
        assert len(self.events) > 0, "no return periods identified"
        assert "me" in self.stats, "mean water depth (key: me) is missing"
        assert "fr" in self.stats, "inundated fraction (key: fr) is missing"

        # CLEANUPS
        self.remap_road_types_to_fewer_classes()
        self.clean_and_interpolate_missing_lane_data()

        gdf_mask = self.create_mask()

        # create dataframe from gdf  #Todo: check why this is necessary
        column_names = list(gdf_mask.columns)
        column_names.remove("geometry")
        df = gdf_mask[column_names]

        self.df = df  # helper dataframe to speedup the analysis
        self.fix_extraordinary_lanes()

        if damage_function == "HZ":
            self.calculate_damage_HZ(events=self.events)

        if damage_function == "OSD":
            self.calculate_damage_OSdaMage(events=self.events)

        if damage_function == "MAN":
            self.calculate_damage_manual_functions(events=self.events,manual_damage_functions=manual_damage_functions)


class event_hazard_network_gdf:  # DEPRECIATED, SEE THE ABOVE CLASSES STRUCTURE!!!
    """A road network gdf with hazard data per event stored in it.

    @Author: Kees van Ginkel, - I made this as an example of how we could develop the code more object-based

    Mandatory attributes:
        *self.events* (set)  : all available unique events
        *self.stats* (set)   : the available statistics
    """

    # Todo check how you can built this on top of geopandas df
    def __init__(
        self, road_gdf, val_cols
    ):  # TODO: DONE, THIS IS ALREADY IMPLEMENTED IN THE NEW DamageNetwork
        """Construct the network gdf and make some handy attributes"""
        # todo self.hazard name
        self.val_cols = val_cols
        self.events = set([x.split("_")[1] for x in val_cols])  # set of unique events
        self.stats = set(
            [x.split("_")[2] for x in val_cols]
        )  # set of hazard info per event
        self.gdf = road_gdf

    def create_mask(
        self,
    ):  # TODO: DONE, THIS IS ALREADY IMPLEMENTED IN THE NEW DamageNetwork
        """
        #Create a mask of only the dataframes with hazard data (to speed-up damage calculations)
        effect: *self.gdf_mask* = mask of only the rows with hazard data
        also returns this value
        """
        # because the fractions are often 0 (also if the rest is nan, this messes up the .isna)
        val_cols_temp = [c for c in self.val_cols if "_fr" not in c]

        gdf_mask = self.gdf.loc[~(self.gdf[val_cols_temp].isna()).all(axis=1)]
        self.gdf_mask = gdf_mask  # todo: not sure if we need to store the mask
        return gdf_mask

    def calculate_damage_HZ(
        self, interpolator, max_damages_huizinga, curve_name="HZ"
    ):  # TODO: DONE, THIS IS ALREADY IMPLEMENTED IN THE NEW DamageNetwork
        """
        Calculate the road damage per event with the Huizinga damage functions
        #uses the mean inundation depth, and the inundated fraction
        Arguments:
            *self.gdf* (see init)
            *interpolator* (SciPy interpolator object) -- the interpolator function that belongs to the damage curve
            *max_damages_HZ* (dictionary) -- dictionary containing the max_damages per road-type and number of lanes, for the Huizinga
                                            damage curves specifically
            *curve (string) -- name of the max_damage dictionary; to save as column names in the output pandas DataFrame ->

        Effect:
            *self.gdf*  : Adds a new column wih
        """
        assert len(self.events) > 0
        assert (
            "me" in self.stats
        )  # mean water depth should be provided #todo if the mean is calculated over the whole or only inundated segment
        assert (
            "fr" in self.stats
        )  # the inundated fraction of the segment should be provided

        # Variable settings (not yet arguments)
        # Todo: Dirty fixes:
        hazard_prefix = "F"
        end = "me"  # indicate that you want to use the mean

        gdf_mask = self.create_mask()
        # create dataframe from gdf
        column_names = list(gdf_mask.columns)
        column_names.remove("geometry")
        df = gdf_mask[column_names]

        # fixing lanes #todo move out this function
        df["lanes_copy"] = df["lanes"].copy()
        df["lanes"] = df["lanes_copy"].where(
            df["lanes_copy"].astype(float) >= 1.0, other=1.0
        )
        df["lanes"] = df["lanes_copy"].where(
            df["lanes_copy"].astype(float) <= 6.0, other=6.0
        )

        df_max_damages_huizinga = pd.DataFrame.from_dict(max_damages_huizinga)
        df["max_dam_hz"] = df_max_damages_huizinga.lookup(df["lanes"], df["road_type"])

        for event in self.events:  # todo self
            df["dam_{}_{}".format(event, curve_name)] = round(
                df["max_dam_hz"].astype(float)  # max damage (euro/km)
                * interpolator(df["{}_{}_{}".format(hazard_prefix, event, end)]).astype(
                    float
                )  # damage curve  (-)
                * df["{}_{}_{}".format(hazard_prefix, event, "fr")].astype(
                    float
                )  # inundated fraction (-)
                * df["length"],
                2,
            )  # length segment (m)

        # Todo: still need to check the units
        logging.warning("Damage calculation units have not been checked!!! TODO")

        # Add the new columns add the right location to the df
        dam_cols = [c for c in df.columns if c.startswith("dam_")]
        self.gdf[dam_cols] = df[dam_cols]
        logging.info(
            "calculate_damage_HZ(): Damage calculation with the Huizinga damage functions was succesfull"
        )

    def calculate_damage_OSdaMage(
        self, interpolators, max_damages
    ):  # TODO: DONE, THIS HAS BEEN IMPLEMENTED
        """
        Calculate the road damage per event with OSdaMage functions
        #uses the mean inundation depth, and the inundated fraction
        Arguments:
            *self.gdf* (see init)
            *interpolators* (list of SciPy interpolator object) -- the interpolator function that belongs ....
                    ... to the damage curve, the keys are taken as the name of the objects
            *max_damages_* (dictionary) -- dictionary containing the max_damages per road-type

        Effect:
            *self.gdf*  : Adds new columns to the dataframe, one for each damage curve. They contain tuples with the
                            0, 25%, 50%, 75% and 100% of maximum damage
        """
        assert len(self.events) > 0
        assert (
            "me" in self.stats
        )  # mean water depth should be provided #todo if the mean is calculated over the whole or only inundated segment
        assert (
            "fr" in self.stats
        )  # the inundated fraction of the segment should be provided

        # Variable settings (not yet arguments)
        # Todo: Dirty fixes:
        hazard_prefix = "F"
        end = "me"  # indicate that you want to use the mean

        interpolators.pop(
            "HZ", None
        )  # drop the Huizinga interpolator if for some reason it is still around

        gdf_mask = self.create_mask()
        # create dataframe from gdf
        column_names = list(gdf_mask.columns)
        column_names.remove("geometry")
        df = gdf_mask[column_names]

        # fixing lanes #todo move out this function
        df["lanes_copy"] = df["lanes"].copy()
        df["lanes"] = df["lanes_copy"].where(
            df["lanes_copy"].astype(float) >= 1.0, other=1.0
        )
        df["lanes"] = df["lanes_copy"].where(
            df["lanes_copy"].astype(float) <= 6.0, other=6.0
        )

        df["tuple"] = [tuple([0] * 5)] * len(df["lanes"])

        # CALCULATE MINIMUM AND MAXIMUM CONSTRUCTION COST PER ROAD TYPE
        # pre-calculation of max damages per percentage (same for each C1-C6 category)
        df["lower_damage"] = (
            df["road_type"].copy().map(max_damages["Lower"])
        )  # i.e. min construction costs
        df["upper_damage"] = (
            df["road_type"].copy().map(max_damages["Upper"])
        )  # i.e. max construction costs

        # create separate column for each percentile of construction costs (is faster then tuple)
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

        columns = []
        for curve_name, interpolator in interpolators.items():
            # print(curve_name, interpolator)
            for event in self.events:
                for percentage in [0, 25, 50, 75, 100]:
                    df["dam_{}_{}_{}".format(percentage, curve_name, event)] = round(
                        df["damage_{}".format(percentage)].astype(
                            float
                        )  # max damage (in euro/km)
                        * interpolator(
                            df["{}_{}_{}".format(hazard_prefix, event, end)]
                        ).astype(
                            float
                        )  # damage curve: fraction f(depth-cm) #Todo check units
                        * df["{}_{}_{}".format(hazard_prefix, event, "fr")].astype(
                            float
                        )  # inundated fraction of the segment
                        * df["length"].astype(float),
                        2,
                    )  # total segment length (m)

                # This wraps it all in tuple again
                df["dam_{}_{}".format(curve_name, event)] = tuple(
                    zip(
                        df["dam_0_{}_{}".format(curve_name, event)],
                        df["dam_25_{}_{}".format(curve_name, event)],
                        df["dam_50_{}_{}".format(curve_name, event)],
                        df["dam_75_{}_{}".format(curve_name, event)],
                        df["dam_100_{}_{}".format(curve_name, event)],
                    )
                )

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

        for curve in other_curves:
            df.loc[df["road_type"] == ("motorway" or "trunk"), curve] = np.nan

        for curve in motorway_curves:
            df.loc[df["road_type"] != ("motorway" or "trunk"), curve] = np.nan

        # Todo: still need to check the units
        logging.warning("Damage calculation units have not been checked!!! TODO")

        # Add the new columns add the right location to the df
        self.gdf[all_dam_cols] = df[all_dam_cols]
        logging.info(
            "calculate_damage_OSdaMage(): Damage calculation with the OSdaMage functions was succesfull"
        )

class ManualDamageFunctions:
    """"
    This class keeps an overview of the manual damage functions

    Default behaviour is to find, load and apply all available functions
    At 22 sept 2022: only implemented workflow for DamageFunction_by_RoadType_by_Lane
    """
    def __init__(self):
        self.available = {} #keys = name of the available functions; values = paths to the folder
        self.loaded = [] #List of DamageFunction objects (or child classes

    def find_damage_functions(self,folder) -> None:
        """Find all available damage functions in the specified folder"""
        assert folder.exists(), 'Folder {} does not contain damage functions'.format(folder)
        for subfolder in folder.iterdir(): #Subfolders contain the damage curves
            if subfolder.is_dir():
                #print(subfolder.stem,subfolder)
                self.available[subfolder.stem] = subfolder
        logging.info('Found {} manual damage curves: \n {}'.format(
            len(self.available.keys()),
            list(self.available.keys())))
        return None

    def load_damage_functions(self):
        """"Load damage functions in Ra2Ce"""
        for name, dir in self.available.items():
            damage_function = DamageFunction_by_RoadType_by_Lane(name=name)
            damage_function.from_input_folder(dir)
            damage_function.set_prefix()
            self.loaded.append(damage_function)
            logging.info("Damage function '{}' loaded from folder {}".format(damage_function.name,dir))






class DamageFunction:
    """
    Generic damage function

    """
    def __init__(self, max_damage=None,damage_fraction=None,
                 name=None,hazard='flood',type='depth_damage',infra_type='road'):
        self.name = name
        self.hazard = hazard
        self.type = type
        self.infra_type = infra_type
        self.max_damage = max_damage #Should be a MaxDamage object
        self.damage_fraction = damage_fraction #Should be a DamageFractionHazardSeverity object
        self.prefix = None #Should be two caracters long at maximum

        #Other attributes (will be added later)
        #self.damage_fraction - x-values correspond to hazard_intenity; y-values correspond to damage fraction [0-1]
        #self.hazard_intensity_unit #the unit of the x-values

        #self.max_damage / reconstruction costs #length unit and width unit
        #asset type
        #price level etc

    def apply(self,df):
        #This functions needs to be specified in child classes
        logging.warning("""This method has not been applied. """)

    def add_max_dam(self,df):
        #This functions needs to be specified in child classes
        logging.warning("""This method has not been applied. """)

    def set_prefix(self):
        self.prefix = self.name[0:2]
        logging.info("The prefix: '{}' refers to curve name '{}' in the results".format(
            self.prefix,self.name
        ))





class DamageFunction_by_RoadType_by_Lane(DamageFunction):
    """
    A damage function that has different max damages per road type, but a uniform damage_fraction curve


    The attributes need to be of the type:
    self.max_damage (MaxDamage_byRoadType_byLane)
    self.damage_fraction (DamageFractionHazardSeverityUniform)

    """

    def __init__(self, max_damage=None, damage_fraction=None,
                 name=None,hazard='flood',type='depth_damage',infra_type='road'):
        # Construct using the parent class __init__
        DamageFunction.__init__(self, max_damage=max_damage,damage_fraction=damage_fraction,
                                name=name,hazard=hazard,type=type,infra_type=infra_type)
        #Do extra stuffs

    def from_input_folder(self,folder_path):
        """Construct a set of damage functions from csv files located in the folder_path

        Arguments:
            *folder_path* (Pathlib Path) : path to folder where csv files can be found
        """
        #Load the max_damage object
        max_damage = MaxDamage_byRoadType_byLane()
        #search in the folder for something *max_damage*
        #folder_path = Path(r"D:\Python\ra2ce\data\1010b_zuid_holland\input\damage_function\test")
        max_dam_path = find_unique_csv_file(folder_path, "max_damage")
        max_damage.from_csv(max_dam_path, sep=';')

        self.max_damage = max_damage

        #Load the damage fraction function
        #search in the folder for something *damage_fraction
        damage_fraction = DamageFractionUniform()
        dam_fraction_path = find_unique_csv_file(folder_path, "hazard_severity")
        damage_fraction.from_csv(dam_fraction_path, sep=';')
        self.damage_fraction = damage_fraction

        damage_fraction.create_interpolator()


    #Todo: these two below functions are maybe better implemented at a lower level?
    def add_max_damage(self,df,prefix=None):
        """"Ads the max damage value to the dataframe"""
        cols = df.columns
        assert "road_type" in cols, "no column 'road type' in df"
        assert "lanes" in cols, "no column 'lanes in df"

        max_damage_data = self.max_damage.data
        df['{}_temp_max_dam'.format(prefix)] = max_damage_data.lookup(df["road_type"],df["lanes"])
        return df

    def calculate_damage(self,df,DamFun_prefix,hazard_prefix,event_prefix):
        """Calculates the damage for one event

        The prefixes are used to find/set the right df columns

        Arguments:
            *df* (pd.Dataframe) : dataframe with road network data
            *DamFun_prefix* : prefix to identify the right damage function e.g. 'A'
            *hazard_prefix* : prefix to identify the right hazard e.g. 'F'
            *event_prefix*  : prefix to identify the right event, e.g. 'EV1'

        """

        interpolator = self.damage_fraction.interpolator #get the interpolator function

        #Find correct columns in dataframe
        result_col = "dam_{}_{}".format(event_prefix,DamFun_prefix)
        max_dam_col = "{}_temp_max_dam".format(DamFun_prefix)
        hazard_severity_col = "{}_{}_me".format(hazard_prefix,event_prefix) #mean is hardcoded now

        df[result_col] = round(
            df[max_dam_col].astype(float) #max damage (euro/m)
            * interpolator(df[hazard_severity_col].astype(float)) # damage curve  (-)
            * df["length"], #segment length (m),
            0) #round to whole numbers
        return df




def find_unique_csv_file(folder_path,part_of_filename):
    """
    Arguments: find unique csv file in a folder, with a given part_of_filename
    Raises a warning if no file can be found, and an error if more than one file is found

    :param folder_path: (pathlib Path) - The folder in which the csv is searched for
    :return: result (pathlib Path) - The path with the csv file
    """
    result = []
    for file in folder_path.iterdir():
        if (part_of_filename in file.stem) and (file.suffix == '.csv'):
            result.append(file)
    if len(result) > 1:
        raise ValueError("Found more then one damage file in {}".format(folder_path))
    elif len(result) == 0:
        logging.warning("Did not found any damage file in {}".format(folder_path))
    else:
        result = result[0]
    return result





class MaxDamage():
    """
    Base class for data containing maximum damage or construction costs data.

    """
    pass

class MaxDamage_byRoadType_byLane(MaxDamage):
    """
    Subclass of MaxDamage, containing max damage per RoadType and per Lane

    Attributes:
        self.name (str) : Name of the damage curve
        self.data (pd.DataFrame) : columns contain number of lanes; rows contain the road types

    Optional attributes:
        self.origin_path (Path) : Path to the file from which the function was constructed
        self.raw_data : The raw data read from the input file


    """
    def __init__(self,name=None,damage_unit=None):
        self.name = name
        self.damage_unit = damage_unit

    def from_csv(self,path: Path,sep=',',output_unit='euro/m') -> None:
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
        self.raw_data = pd.read_csv(path,index_col='Road_type \ lanes',sep=sep)
        self.origin_path = path #to track the original path from which the object was constructed; maybe also date?

        ###Determine units
        units = self.raw_data.loc['unit',:].unique() #identify the unique units
        assert len(units) == 1, 'Columns in the max damage csv seem to have different units, ra2ce cannot handle this'
        #case only one unique unit is identified
        self.damage_unit = units[0] #should have the structure 'x/y' , e.g. euro/m, dollar/yard

        self.data = self.raw_data.drop('unit')
        self.data = self.data.astype('float')

        #assume road types are in the rows; lane numbers in the columns
        self.road_types = list(self.data.index) #to method
        #assumes that the columns containst the lanes
        self.data.columns = self.data.columns.astype('int')


        if self.damage_unit != 'output_unit':
            self.convert_length_unit() #convert the unit


    def convert_length_unit(self,desired_unit='euro/m') -> None:
        """Converts max damage values to a different unit
        Arguments:
            self.damage_unit (implicit)
            *desired_unit* (string)

        Effect: converts the values in self.data; and sets the new damage_unit

        Returns: the factor by which the original unit has been scaled

        """
        if desired_unit == self.damage_unit:
            logging.info('Input damage units are already in the desired format')
            return None

        original_length_unit = self.damage_unit.split('/')[1]
        target_length_unit = desired_unit.split('/')[1]

        if (original_length_unit == 'km' and target_length_unit == 'm'):
            scaling_factor = 1/1000
            self.data = self.data * scaling_factor
            logging.info('Damage data from {} was scaled by a factor {}, to convert from {} to {}'.format(
                self.origin_path, scaling_factor,self.damage_unit,desired_unit))
            self.damage_unit = desired_unit
            return None
        else:
            logging.warning('Damage scaling from {} to {} is not supported'.format(self.damage_unit,desired_unit))
            return None

class DamageFraction():
    """
    Base class for data containing maximum damage or construction costs data.

    """
    pass

class DamageFractionUniform(DamageFraction):
    """
    Uniform: assuming the same curve for
    each road type and lane numbers and any other metadata


    self.raw_data (pd.DataFrame) : Raw data from the csv file
    self.data (pd.DataFrame) : index = hazard severity (e.g. flood depth); column 0 = damage fraction

    """
    def __init__(self,name=None,hazard_unit=None):
        self.name = name
        self.hazard_unit = hazard_unit
        self.interpolator = None

    def from_csv(self,path: Path,sep=',',desired_unit='m') -> None:
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
        self.raw_data = pd.read_csv(path,index_col=0,sep=sep)
        self.origin_path = path #to track the original path from which the object was constructed; maybe also date?

        #identify unit and drop from data
        self.hazard_unit = self.raw_data.index[0]
        self.data = self.raw_data.drop(self.hazard_unit) #Todo: This could also be a series instead of DataFrame

        #convert data to floats
        self.data = self.data.astype('float')
        self.data.index = self.data.index.astype('float')

        self.convert_hazard_severity_unit()

    def convert_hazard_severity_unit(self,desired_unit='m') -> None:
        """Converts hazard severity values to a different unit
        Arguments:
            self.hazard_unit - implicit (string)
            *desired_unit* (string)

        Effect: converts the values in self.data; and sets the new damage_unit to the desired unit

        """
        if desired_unit == self.hazard_unit:
            logging.info('Damage units are already in the desired format {}'.format(desired_unit))
            return None

        if (self.hazard_unit == 'cm' and desired_unit == 'm'):
            scaling_factor = 1/100
            self.data.index = self.data.index * scaling_factor
            logging.info('Hazard severity from {} data was scaled by a factor {}, to convert from {} to {}'.format(
                self.origin_path, scaling_factor,self.hazard_unit,desired_unit))
            self.damage_unit = desired_unit
            return None
        else:
            logging.warning('Hazard severity scaling from {} to {} is not  supported'.format(self.hazard_unit,desired_unit))
            return None

    def create_interpolator(self):
        """ Create interpolator object from loaded data
        sets result to self.interpolator (Scipy interp1d)
        """
        from scipy.interpolate import interp1d
        x_values = self.data.index.values
        y_values = self.data.values[:,0]

        self.interpolator = interp1d(x=x_values,y=y_values,
                fill_value=(y_values[0],y_values[-1]), #fraction damage (y) if hazard severity (x) is outside curve range
                bounds_error=False)

        return None

    def __repr__(self):
        if self.interpolator:
            string = 'DamageFractionUniform with name: ' + self.name + ' interpolator: {}'.format(
                list(zip(self.interpolator.y, self.interpolator.x)))
        else:
            string = 'DamageFractionUniform with name: ' +  self.name
        return string









#Tests:
def test_construct_max_damage():
    max_damage = MaxDamage_byRoadType_byLane()
    path = Path(r"D:\Python\ra2ce\data\1010b_zuid_holland\input\damage_function\test\huizinga_max_damage.csv")
    max_damage.from_csv(path,sep=';')
    return max_damage

def test_construct_damage_fraction():
    damage_fraction = DamageFractionUniform()
    path = Path(r"D:\Python\ra2ce\data\1010b_zuid_holland\input\damage_function\test\huizinga_damage_fraction_hazard_severity.csv")
    damage_fraction.from_csv(path,sep=';')
    return damage_fraction

#max_damage = test_construct_max_damage()

#max_damage = test_construct_damage_fraction()




class EffectivenessMeasures:
    """This is a namespace for methods to calculate effectiveness of measures"""

    def __init__(self, config, analysis):
        self.analysis = analysis
        self.config = config
        self.return_period = analysis["return_period"]  # years
        self.repair_costs = analysis["repair_costs"]  # euro
        self.evaluation_period = analysis["evaluation_period"]  # years
        self.interest_rate = analysis["interest_rate"] / 100  # interest rate
        self.climate_factor = analysis["climate_factor"] / analysis["climate_period"]
        self.btw = 1.21  # VAT multiplication factor to include taxes

        # perform checks on input while initializing class
        if analysis["file_name"] is None:
            logging.error(
                "Effectiveness of measures calculation:... No input file configured. "
                "Please define an input file in the analysis.ini file "
            )
            quit()
        elif analysis["file_name"].split(".")[1] != "shp":
            logging.error(
                "Effectiveness of measures calculation:... Wrong input file configured. "
                "Extension of input file is -{}-, needs to be -shp- (shapefile)".format(
                    analysis["file_name"].split(".")[1]
                )
            )
            quit()
        elif (
            os.path.exists(config["input"] / "direct" / analysis["file_name"]) is False
        ):
            logging.error(
                "Effectiveness of measures calculation:... Input file doesnt exist..."
                " please place file in the following folder: {}".format(
                    config["input"] / "direct"
                )
            )
            quit()
        elif (
            os.path.exists(config["input"] / "direct" / "effectiveness_measures.csv")
            is False
        ):
            logging.error(
                "Effectiveness of measures calculation:... lookup table with effectiveness of measures doesnt exist..."
                " Please place the effectiveness_measures.csv file in the following folder: {}".format(
                    config["input"] / "direct"
                )
            )
            quit()

    @staticmethod
    def load_effectiveness_table(path):
        """This function loads a CSV table containing effectiveness of the different aspects for a number of strategies"""
        file_path = path / "effectiveness_measures.csv"
        df_lookup = pd.read_csv(file_path, index_col="strategies")
        return df_lookup.transpose().to_dict()

    @staticmethod
    def create_feature_table(file_path):
        """This function loads a table of features from the input folder"""
        logging.info("Loading feature dataframe...")
        gdf = gpd.read_file(file_path)
        logging.info("Dataframe loaded...")

        # cleaning up dataframe
        df = pd.DataFrame(gdf.drop(columns="geometry"))
        df = df[df["LinkNr"] != 0]
        df = df.sort_values(by=["LinkNr", "TARGET_FID"])
        df = df.rename(
            columns={
                "ver_hoog_m": "ver_hoger_m",
                "hwaafwho_m": "hwa_afw_ho_m",
                "slope_15_m": "slope_0015_m",
                "slope_1_m": "slope_001_m",
                "TARGET_FID": "target_fid",
                "Length": "length",
            }
        )
        df = df[
            [
                "LinkNr",
                "target_fid",
                "length",
                "dichtbij_m",
                "ver_hoger_m",
                "hwa_afw_ho_m",
                "gw_hwa_m",
                "slope_0015_m",
                "slope_001_m",
            ]
        ]

        # save as csv
        path, file = os.path.split(file_path)
        df.to_csv(os.path.join(path, file.replace(".shp", ".csv")), index=False)
        return df

    @staticmethod
    def load_table(path, file):
        """This method reads the dataframe created from"""
        file_path = path / file
        df = pd.read_csv(file_path)
        return df

    @staticmethod
    def knmi_correction(df, duration=60):
        """This function corrects the length of each segment depending on a KNMI factor.
        This factor is calculated using an exponential relation and was calculated using an analysis on all line elements
        a relation is establisched for a 10 minute or 60 minute rainfall period
        With a boolean you can decide to export length or the coefficient itself
        max 0.26 en 0.17
        """
        if duration not in [10, 60]:
            logging.error("Wrong duration configured, has to be 10 or 60")
            quit()
        logging.info(
            "Applying knmi length correction with duration of rainfall of -{}- minutes".format(
                duration
            )
        )

        coefficients_lookup = {
            10: {"a": 1.004826523, "b": -0.000220199, "max": 0.17},
            60: {"a": 1.012786829, "b": -0.000169182, "max": 0.26},
        }

        coefficient = coefficients_lookup[duration]
        df["coefficient"] = coefficient["a"] * np.exp(coefficient["b"] * df["length"])
        df["coefficient"] = df["coefficient"].where(
            df["length"].astype(float) <= 8000, other=coefficient["max"]
        )
        return df

    @staticmethod
    def calculate_effectiveness(df, name="standard"):
        """This function calculates effectiveness, based on a number of columns:
        'dichtbij_m', 'ver_hoger_m', 'hwa_afw_ho_m', 'gw_hwa_m', slope_0015_m' and 'slope_001_m'
        and contains the following steps:
        1. calculate the max of ver_hoger, hwa_afw_ho and gw_hwa columns --> verweg
        2. calculate maximum of slope0015 / 2 and slope 001 columns --> verkant
        3. calculate max of verweg, verkant and dichtbij
        4. calculate sum of verweg, verkant and dichtbij
        5. aggregate (sum) of values to LinkNr
        """
        # perform calculation of max length of ver weg elements and slope elements:
        df["slope_0015_m2"] = df["slope_0015_m"] / 2
        df["verweg_max"] = (
            df[["ver_hoger_m", "hwa_afw_ho_m", "gw_hwa_m"]].values.max(1).round(0)
        )
        df["verkant_max"] = df[["slope_0015_m2", "slope_001_m"]].values.max(1).round(0)

        # calculate gevoelig max and dum
        df["{}_gevoelig_max".format(name)] = (
            df[["verweg_max", "verkant_max", "dichtbij_m"]].values.max(1).round(0)
        )
        df["{}_gevoelig_sum".format(name)] = (
            df["verweg_max"] + df["verkant_max"] + df["dichtbij_m"]
        )

        # aggregate to link nr
        new_df = df[
            [
                "LinkNr",
                "length",
                "dichtbij_m",
                "ver_hoger_m",
                "hwa_afw_ho_m",
                "gw_hwa_m",
                "verweg_max",
                "verkant_max",
                "{}_gevoelig_max".format(name),
                "{}_gevoelig_sum".format(name),
            ]
        ]
        new_df = new_df.groupby(["LinkNr"]).sum()
        new_df["LinkNr"] = new_df.index
        new_df = new_df.reset_index(drop=True)

        return new_df[
            [
                "LinkNr",
                "length",
                "dichtbij_m",
                "ver_hoger_m",
                "hwa_afw_ho_m",
                "gw_hwa_m",
                "verweg_max",
                "verkant_max",
                "{}_gevoelig_max".format(name),
                "{}_gevoelig_sum".format(name),
            ]
        ]

    def calculate_strategy_effectiveness(self, df, effectiveness_dict):
        """This function calculates the efficacy for each strategy"""

        columns = [
            "dichtbij",
            "ver_hoger",
            "hwa_afw_ho",
            "gw_hwa",
            "slope_0015",
            "slope_001",
        ]

        # calculate standard effectiveness without factors
        df_total = self.calculate_effectiveness(df, name="standard")

        df_blockage = pd.read_csv(
            self.config["input"] / "direct" / "blockage_costs.csv"
        )
        df_total = df_total.merge(df_blockage, how="left", on="LinkNr")
        df_total["length"] = df_total[
            "afstand"
        ]  # TODO Remove this line as this is probably incorrect, just as a check

        # start iterating over different strategies in lookup dictionary
        for strategy in effectiveness_dict:
            logging.info("Calculating effectiveness of strategy: {}".format(strategy))
            lookup_dict = effectiveness_dict[strategy]
            df_temp = df.copy()

            # apply the effectiveness factor as read from the lookup table on each column:
            for col in columns:
                df_temp[col + "_m"] = df_temp[col + "_m"] * (1 - lookup_dict[col])

            # calculate the effectiveness and add as a new column to total dataframe
            df_new = self.calculate_effectiveness(df_temp, name=strategy)
            df_new = df_new.drop(
                columns={
                    "length",
                    "dichtbij_m",
                    "ver_hoger_m",
                    "hwa_afw_ho_m",
                    "gw_hwa_m",
                    "verweg_max",
                    "verkant_max",
                }
            )
            df_total = df_total.merge(df_new, how="left", on="LinkNr")

        return df_total

    def calculate_cost_reduction(self, df, effectiveness_dict):
        """This function calculates the yearly costs and possible reduction"""

        strategies = [strategy for strategy in effectiveness_dict]
        strategies.insert(0, "standard")

        # calculate costs
        for strategy in strategies:
            if strategy != "standard":
                df["max_effectiveness_{}".format(strategy)] = 1 - (
                    df["{}_gevoelig_sum".format(strategy)] / df["standard_gevoelig_sum"]
                )
            df["return_period"] = self.return_period * df["coefficient"]
            df["repair_costs_{}".format(strategy)] = (
                df["{}_gevoelig_max".format(strategy)] * self.repair_costs
            )
            df["blockage_costs_{}".format(strategy)] = df["blockage_costs"]
            df["yearly_repair_costs_{}".format(strategy)] = (
                df["repair_costs_{}".format(strategy)] / df["return_period"]
            )
            if strategy == "standard":
                df["yearly_blockage_costs_{}".format(strategy)] = (
                    df["blockage_costs_{}".format(strategy)] / df["return_period"]
                )
            else:
                df["yearly_blockage_costs_{}".format(strategy)] = (
                    df["blockage_costs_{}".format(strategy)]
                    / df["return_period"]
                    * (1 - df["max_effectiveness_{}".format(strategy)])
                )
            df["total_costs_{}".format(strategy)] = (
                df["yearly_repair_costs_{}".format(strategy)]
                + df["yearly_blockage_costs_{}".format(strategy)]
            )
            if strategy != "standard":
                df["reduction_repair_costs_{}".format(strategy)] = (
                    df["yearly_repair_costs_standard"]
                    - df["yearly_repair_costs_{}".format(strategy)]
                )
                df["reduction_blockage_costs_{}".format(strategy)] = (
                    df["yearly_blockage_costs_standard"]
                    - df["yearly_blockage_costs_{}".format(strategy)]
                )
                df["reduction_costs_{}".format(strategy)] = (
                    df["total_costs_standard"] - df["total_costs_{}".format(strategy)]
                )
                df["effectiveness_{}".format(strategy)] = 1 - (
                    df["total_costs_{}".format(strategy)] / df["total_costs_standard"]
                )
        return df

    def cost_benefit_analysis(self, effectiveness_dict):
        """This method performs cost benefit analysis"""

        def calc_npv(x, cols):
            pv = np.npv(self.interest_rate, [0] + list(x[cols]))
            return pv

        def calc_npv_factor(factor):
            cols = np.linspace(
                1,
                1 + (factor * self.evaluation_period),
                self.evaluation_period,
                endpoint=False,
            )
            return np.npv(self.interest_rate, [0] + list(cols))

        def calc_cash_flow(x, cols):
            cash_flow = x[cols].sum() + x["investment"]
            return cash_flow

        df_cba = pd.DataFrame.from_dict(effectiveness_dict).transpose()
        df_cba["strategy"] = df_cba.index
        df_cba = df_cba.drop(
            columns=[
                "dichtbij",
                "ver_hoger",
                "hwa_afw_ho",
                "gw_hwa",
                "slope_0015",
                "slope_001",
            ]
        )
        df_cba["investment"] = df_cba["investment"] * -1

        df_cba["lifespan"] = df_cba["lifespan"].astype(int)
        for col in ["om_pv", "pv", "cash_flow"]:
            df_cba.insert(0, col, 0)

        # add years
        for year in range(1, self.evaluation_period + 1):
            df_cba[str(year)] = df_cba["investment"].where(
                np.mod(year, df_cba["lifespan"]) == 0, other=0
            )
        year_cols = [str(year) for year in range(1, self.evaluation_period + 1)]

        df_cba["om_pv"] = df_cba.apply(lambda x: calc_npv(x, year_cols), axis=1)
        df_cba["pv"] = df_cba["om_pv"] + df_cba["investment"]
        df_cba["cash_flow"] = df_cba.apply(
            lambda x: calc_cash_flow(x, year_cols), axis=1
        )
        df_cba["costs"] = df_cba["pv"] * self.btw
        df_cba["costs_pmt"] = (
            np.pmt(
                self.interest_rate, df_cba["lifespan"], df_cba["investment"], when="end"
            )
            * self.btw
        )
        df_cba = df_cba.round(2)

        costs_dict = df_cba[["costs", "on_column"]].to_dict()
        costs_dict["npv_factor"] = calc_npv_factor(self.climate_factor)

        return df_cba, costs_dict

    @staticmethod
    def calculate_strategy_costs(df, costs_dict):
        """Method to calculate costs, benefits with net present value"""

        costs = costs_dict["costs"]
        columns = costs_dict["on_column"]

        def columns_check(df, columns):
            cols_check = []
            for col in columns:
                cols_check.extend(columns[col].split(";"))
            df_cols = list(df.columns)

            if any([True for col in cols_check if col not in df_cols]):
                cols = [col for col in cols_check if col not in df_cols]
                logging.error(
                    "Wrong column configured in effectiveness_measures csv file. column {} is not available in imported sheet.".format(
                        cols
                    )
                )
                quit()
            else:
                return True

        columns_check(df, columns)
        strategies = {col: columns[col].split(";") for col in columns}

        for strategy in strategies:
            df["{}_benefits".format(strategy)] = (
                df["reduction_costs_{}".format(strategy)] * costs_dict["npv_factor"]
            )
            select_col = strategies[strategy]
            if len(select_col) == 1:
                df["{}_costs".format(strategy)] = (
                    df[select_col[0]] * costs[strategy] * -1 / 1000
                )
            if len(select_col) > 1:
                df["{}_costs".format(strategy)] = (
                    (df[select_col[0]] - df[select_col[1]])
                    * costs[strategy]
                    * -1
                    / 1000
                )
                df["{}_costs".format(strategy)] = df["{}_costs".format(strategy)].where(
                    df["{}_costs".format(strategy)] > 1, other=np.nan
                )
            df["{}_bc_ratio".format(strategy)] = (
                df["{}_benefits".format(strategy)] / df["{}_costs".format(strategy)]
            )

        return df
