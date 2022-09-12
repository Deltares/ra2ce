# -*- coding: utf-8 -*-
"""
Created on 26-7-2021
"""

import geopandas as gpd
import logging
import time
import numpy as np
import pandas as pd
import os, sys
from numpy import object as np_object

from .direct_utils import *
from .direct_lookup import LookUp as lookup


folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder)


class DirectAnalyses:
    def __init__(self, config, graphs):
        self.config = config
        self.graphs = graphs

    def road_damage(self, analysis):
        """
        Calculates the road damage

        :param analysis:
        :return:
        """
        rd = RoadDamage() #Creates a Road Damage object, the methods of this object are used to do the damage calculation
        gdf = self.graphs['base_network_hazard']
        if self.graphs['base_network_hazard'] is None:
            gdf = gpd.read_feather(self.config['files']['base_network_hazard'])

        # TODO: This should probably not be done here, but at the create network function
        # reduce the number of road types (col 'infra_type') to smaller number of road_types for which damage curves exist
        road_mapping_dict = lookup.road_mapping() #The lookup class contains all kinds of data
        gdf.rename(columns={'highway': 'infra_type'}, inplace=True)
        gdf['road_type'] = gdf['infra_type']
        gdf = gdf.replace({"road_type": road_mapping_dict})

        # TODO sometimes there are edges with multiple mappings ?? To check this
        # TODO I, Kees think this is a dangerous cleanup procedure with possible unexpected outcomes
        # cleanup of gdf
        for column in gdf.columns:
            gdf[column] = gdf[column].apply(rd.apply_cleanup) #Todo: rename function, this is too vague.

        # cleanup and complete the lane data.
        ### Try to convert all data to floats
        try:
            gdf.lanes = gdf.lanes.astype('float') #floats instead of ints because ints cannot be nan.
        except:
            logging.warning('Available lane data cannot simply be converted to float/int, RA2CE will try a clean-up.')
            gdf.lanes = clean_lane_data(gdf.lanes)

        gdf.lanes = gdf.lanes.round(0) #round to nearest integer, but save as float format
        nans = gdf.lanes.isnull() #boolean with trues for all nans, i.e. all road segements without lane data
        if nans.sum() > 0:
            logging.warning("""Of the {} road segments, only {} had lane data, so for {} the '
                            lane data will be interpolated from the existing data""".format(
                len(gdf.lanes),(~nans).sum(),nans.sum()))
            lane_stats = create_summary_statistics(gdf)

            #Replace the missing lane data the neat way (without pandas SettingWithCopyWarning)
            lane_nans_mask = gdf.lanes.isnull()
            gdf.loc[lane_nans_mask, 'lanes'] = gdf.loc[lane_nans_mask, 'road_type'].replace(lane_stats)
            logging.warning('Interpolated the missing lane data as follows: {}'.format(lane_stats))

            #Todo: write the whole interpolater object

            #This worked but raises an error
            #lane_nans = gdf[gdf.lanes.isnull()]  # mask all nans in lane data
            #lane_nans['lanes'] =  lane_nans['road_type'].replace(lane_stats)
            #gdf.loc[lane_nans.index, :] = lane_nans

            # Todo: What if for one road type all lane data is missing?
            # Todo: we could script a seperate work-around for this situation, for now we just raise an assertion
            assert not (np.nan in gdf.lanes.unique()) #all nans should be replaced

        # calculate direct damage
        road_gdf_damage = rd.calculate_direct_damage(gdf)
        return road_gdf_damage

    def effectiveness_measures(self, analysis):
        """ This function calculated the efficiency of measures. Input is a csv file with efficiency
        and a list of different aspects you want to check.
         """
        em = EffectivenessMeasures(self.config, analysis)
        effectiveness_dict = em.load_effectiveness_table(self.config['input'] / 'direct')

        if self.graphs['base_network_hazard'] is None:
            gdf_in = gpd.read_feather(self.config['files']['base_network_hazard'])

        if analysis['create_table'] is True:
            df = em.create_feature_table(self.config['input'] / 'direct' / analysis['file_name'])
        else:
            df = em.load_table(self.config['input'] / 'direct', analysis['file_name'].replace('.shp', '.csv'))

        df = em.calculate_strategy_effectiveness(df, effectiveness_dict)
        df = em.knmi_correction(df)
        df_cba, costs_dict = em.cost_benefit_analysis(effectiveness_dict)
        df_cba.round(2).to_csv(self.config['output'] / analysis['analysis'] / 'cost_benefit_analysis.csv', decimal=',', sep=';', index=False, float_format='%.2f')
        df = em.calculate_cost_reduction(df, effectiveness_dict)
        df_costs = em.calculate_strategy_costs(df, costs_dict)
        df_costs = df_costs.astype(float).round(2)
        df_costs.to_csv(self.config['output'] / analysis['analysis'] / 'output_analysis.csv', decimal=',', sep=';', index=False, float_format='%.2f')
        gdf = gdf_in.merge(df, how='left', on='LinkNr')
        return gdf

    def execute(self):
        """Executes the direct analysis."""
        for analysis in self.config['direct']:
            logging.info(f"----------------------------- Started analyzing '{analysis['name']}'  -----------------------------")
            starttime = time.time()

            if analysis['analysis'] == 'direct':

                gdf = self.road_damage(analysis)

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


class EffectivenessMeasures:
    """ This is a namespace for methods to calculate effectiveness of measures """

    def __init__(self, config, analysis):
        self.analysis = analysis
        self.config = config
        self.return_period = analysis['return_period']  # years
        self.repair_costs = analysis['repair_costs']  # euro
        self.evaluation_period = analysis['evaluation_period']  # years
        self.interest_rate = analysis['interest_rate']/100  # interest rate
        self.climate_factor = analysis['climate_factor'] / analysis['climate_period']
        self.btw = 1.21  # VAT multiplication factor to include taxes

        # perform checks on input while initializing class
        if analysis['file_name'] is None:
            logging.error('Effectiveness of measures calculation:... No input file configured. '
                          'Please define an input file in the analysis.ini file ')
            quit()
        elif analysis['file_name'].split('.')[1] != 'shp':
            logging.error('Effectiveness of measures calculation:... Wrong input file configured. '
                          'Extension of input file is -{}-, needs to be -shp- (shapefile)'.format(analysis['file_name'].split('.')[1]))
            quit()
        elif os.path.exists(config['input'] / 'direct' / analysis['file_name']) is False:
            logging.error('Effectiveness of measures calculation:... Input file doesnt exist...'
                          ' please place file in the following folder: {}'.format(config['input'] / 'direct'))
            quit()
        elif os.path.exists(config['input'] / 'direct' / 'effectiveness_measures.csv') is False:
            logging.error('Effectiveness of measures calculation:... lookup table with effectiveness of measures doesnt exist...'
                          ' Please place the effectiveness_measures.csv file in the following folder: {}'.format(config['input'] / 'direct'))
            quit()

    @staticmethod
    def load_effectiveness_table(path):
        """ This function loads a CSV table containing effectiveness of the different aspects for a number of strategies"""
        file_path = path / 'effectiveness_measures.csv'
        df_lookup = pd.read_csv(file_path, index_col='strategies')
        return df_lookup.transpose().to_dict()

    @staticmethod
    def create_feature_table(file_path):
        """ This function loads a table of features from the input folder
         """
        logging.info('Loading feature dataframe...')
        gdf = gpd.read_file(file_path)
        logging.info('Dataframe loaded...')

        # cleaning up dataframe
        df = pd.DataFrame(gdf.drop(columns='geometry'))
        df = df[df['LinkNr'] != 0]
        df = df.sort_values(by=['LinkNr', 'TARGET_FID'])
        df = df.rename(columns={'ver_hoog_m': 'ver_hoger_m', 'hwaafwho_m': 'hwa_afw_ho_m',
                                'slope_15_m': 'slope_0015_m', 'slope_1_m': 'slope_001_m',
                                'TARGET_FID': 'target_fid', 'Length': 'length'})
        df = df[['LinkNr', 'target_fid', 'length', 'dichtbij_m', 'ver_hoger_m', 'hwa_afw_ho_m', 'gw_hwa_m',
                 'slope_0015_m', 'slope_001_m']]

        # save as csv
        path, file = os.path.split(file_path)
        df.to_csv(os.path.join(path, file.replace('.shp', '.csv')), index=False)
        return df

    @staticmethod
    def load_table(path, file):
        """ This method reads the dataframe created from  """
        file_path = path / file
        df = pd.read_csv(file_path)
        return df

    @staticmethod
    def knmi_correction(df, duration=60):
        """ This function corrects the length of each segment depending on a KNMI factor.
            This factor is calculated using an exponential relation and was calculated using an analysis on all line elements
            a relation is establisched for a 10 minute or 60 minute rainfall period
            With a boolean you can decide to export length or the coefficient itself
            max 0.26 en 0.17
            """
        if duration not in [10, 60]:
            logging.error('Wrong duration configured, has to be 10 or 60')
            quit()
        logging.info('Applying knmi length correction with duration of rainfall of -{}- minutes'.format(duration))

        coefficients_lookup = {10: {'a': 1.004826523,
                                    'b': -0.000220199,
                                    'max': 0.17},
                               60: {'a': 1.012786829,
                                    'b': -0.000169182,
                                    'max': 0.26}}

        coefficient = coefficients_lookup[duration]
        df['coefficient'] = coefficient['a'] * np.exp(coefficient['b'] * df['length'])
        df['coefficient'] = df['coefficient'].where(df['length'].astype(float) <= 8000, other=coefficient['max'])
        return df

    @staticmethod
    def calculate_effectiveness(df, name='standard'):
        """ This function calculates effectiveness, based on a number of columns:
         'dichtbij_m', 'ver_hoger_m', 'hwa_afw_ho_m', 'gw_hwa_m', slope_0015_m' and 'slope_001_m'
         and contains the following steps:
         1. calculate the max of ver_hoger, hwa_afw_ho and gw_hwa columns --> verweg
         2. calculate maximum of slope0015 / 2 and slope 001 columns --> verkant
         3. calculate max of verweg, verkant and dichtbij
         4. calculate sum of verweg, verkant and dichtbij
         5. aggregate (sum) of values to LinkNr
         """
        # perform calculation of max length of ver weg elements and slope elements:
        df['slope_0015_m2'] = df['slope_0015_m'] / 2
        df['verweg_max'] = df[['ver_hoger_m', 'hwa_afw_ho_m', 'gw_hwa_m']].values.max(1).round(0)
        df['verkant_max'] = df[['slope_0015_m2', 'slope_001_m']].values.max(1).round(0)

        # calculate gevoelig max and dum
        df['{}_gevoelig_max'.format(name)] = df[['verweg_max', 'verkant_max', 'dichtbij_m']].values.max(1).round(0)
        df['{}_gevoelig_sum'.format(name)] = df['verweg_max'] + df['verkant_max'] + df['dichtbij_m']

        # aggregate to link nr
        new_df = df[['LinkNr', 'length', 'dichtbij_m', 'ver_hoger_m', 'hwa_afw_ho_m', 'gw_hwa_m', 'verweg_max', 'verkant_max', '{}_gevoelig_max'.format(name), '{}_gevoelig_sum'.format(name)]]
        new_df = new_df.groupby(['LinkNr']).sum()
        new_df['LinkNr'] = new_df.index
        new_df = new_df.reset_index(drop=True)

        return new_df[['LinkNr',  'length', 'dichtbij_m', 'ver_hoger_m', 'hwa_afw_ho_m', 'gw_hwa_m', 'verweg_max', 'verkant_max', '{}_gevoelig_max'.format(name), '{}_gevoelig_sum'.format(name)]]

    def calculate_strategy_effectiveness(self, df, effectiveness_dict):
        """ This function calculates the efficacy for each strategy  """

        columns = ['dichtbij', 'ver_hoger', 'hwa_afw_ho', 'gw_hwa', 'slope_0015', 'slope_001']

        # calculate standard effectiveness without factors
        df_total = self.calculate_effectiveness(df, name='standard')

        df_blockage = pd.read_csv(self.config['input'] / 'direct' / 'blockage_costs.csv')
        df_total = df_total.merge(df_blockage, how='left', on='LinkNr')
        df_total['length'] = df_total['afstand'] # TODO Remove this line as this is probably incorrect, just as a check

        # start iterating over different strategies in lookup dictionary
        for strategy in effectiveness_dict:
            logging.info('Calculating effectiveness of strategy: {}'.format(strategy))
            lookup_dict = effectiveness_dict[strategy]
            df_temp = df.copy()

            # apply the effectiveness factor as read from the lookup table on each column:
            for col in columns:
                df_temp[col+'_m'] = df_temp[col+'_m'] * (1 - lookup_dict[col])

            # calculate the effectiveness and add as a new column to total dataframe
            df_new = self.calculate_effectiveness(df_temp, name=strategy)
            df_new = df_new.drop(columns={'length', 'dichtbij_m', 'ver_hoger_m', 'hwa_afw_ho_m', 'gw_hwa_m', 'verweg_max','verkant_max'})
            df_total = df_total.merge(df_new, how='left', on='LinkNr')

        return df_total

    def calculate_cost_reduction(self, df, effectiveness_dict):
        """ This function calculates the yearly costs and possible reduction """

        strategies = [strategy for strategy in effectiveness_dict]
        strategies.insert(0, 'standard')

        # calculate costs
        for strategy in strategies:
            if strategy != 'standard':
                df['max_effectiveness_{}'.format(strategy)] = 1 - (df['{}_gevoelig_sum'.format(strategy)] / df['standard_gevoelig_sum'])
            df['return_period'] = self.return_period * df['coefficient']
            df['repair_costs_{}'.format(strategy)] = df['{}_gevoelig_max'.format(strategy)] * self.repair_costs
            df['blockage_costs_{}'.format(strategy)] = df['blockage_costs']
            df['yearly_repair_costs_{}'.format(strategy)] = df['repair_costs_{}'.format(strategy)] / df['return_period']
            if strategy == 'standard':
                df['yearly_blockage_costs_{}'.format(strategy)] = df['blockage_costs_{}'.format(strategy)] / df['return_period']
            else:
                df['yearly_blockage_costs_{}'.format(strategy)] = df['blockage_costs_{}'.format(strategy)] / df['return_period'] * (1 - df['max_effectiveness_{}'.format(strategy)])
            df['total_costs_{}'.format(strategy)] = df['yearly_repair_costs_{}'.format(strategy)] + df['yearly_blockage_costs_{}'.format(strategy)]
            if strategy != 'standard':
                df['reduction_repair_costs_{}'.format(strategy)] = df['yearly_repair_costs_standard'] - df['yearly_repair_costs_{}'.format(strategy)]
                df['reduction_blockage_costs_{}'.format(strategy)] = df['yearly_blockage_costs_standard'] - df['yearly_blockage_costs_{}'.format(strategy)]
                df['reduction_costs_{}'.format(strategy)] = df['total_costs_standard'] - df['total_costs_{}'.format(strategy)]
                df['effectiveness_{}'.format(strategy)] = 1 - (df['total_costs_{}'.format(strategy)] / df['total_costs_standard'])
        return df

    def cost_benefit_analysis(self, effectiveness_dict):
        """ This method performs cost benefit analysis """

        def calc_npv(x, cols):
            pv = np.npv(self.interest_rate, [0] + list(x[cols]))
            return pv

        def calc_npv_factor(factor):
            cols = np.linspace(1, 1 + (factor * self.evaluation_period), self.evaluation_period, endpoint=False)
            return np.npv(self.interest_rate, [0] + list(cols))

        def calc_cash_flow(x, cols):
            cash_flow = x[cols].sum() + x['investment']
            return cash_flow

        df_cba = pd.DataFrame.from_dict(effectiveness_dict).transpose()
        df_cba['strategy'] = df_cba.index
        df_cba = df_cba.drop(columns=['dichtbij', 'ver_hoger', 'hwa_afw_ho', 'gw_hwa', 'slope_0015', 'slope_001'])
        df_cba['investment'] = df_cba['investment'] * -1

        df_cba['lifespan'] = df_cba['lifespan'].astype(int)
        for col in ['om_pv', 'pv', 'cash_flow']:
            df_cba.insert(0, col, 0)

        # add years
        for year in range(1, self.evaluation_period+1):
            df_cba[str(year)] = df_cba['investment'].where(np.mod(year, df_cba['lifespan']) == 0, other=0)
        year_cols = [str(year) for year in range(1, self.evaluation_period+1)]

        df_cba['om_pv'] = df_cba.apply(lambda x: calc_npv(x, year_cols), axis=1)
        df_cba['pv'] = df_cba['om_pv'] + df_cba['investment']
        df_cba['cash_flow'] = df_cba.apply(lambda x: calc_cash_flow(x, year_cols), axis=1)
        df_cba['costs'] = df_cba['pv'] * self.btw
        df_cba['costs_pmt'] = np.pmt(self.interest_rate, df_cba['lifespan'], df_cba['investment'], when='end') * self.btw
        df_cba = df_cba.round(2)

        costs_dict = df_cba[['costs', 'on_column']].to_dict()
        costs_dict['npv_factor'] = calc_npv_factor(self.climate_factor)

        return df_cba, costs_dict

    @staticmethod
    def calculate_strategy_costs(df, costs_dict):
        """ Method to calculate costs, benefits with net present value """

        costs = costs_dict['costs']
        columns = costs_dict['on_column']

        def columns_check(df, columns):
            cols_check = []
            for col in columns:
                cols_check.extend(columns[col].split(';'))
            df_cols = list(df.columns)

            if any([True for col in cols_check if col not in df_cols]):
                cols = [col for col in cols_check if col not in df_cols]
                logging.error('Wrong column configured in effectiveness_measures csv file. column {} is not available in imported sheet.'.format(cols))
                quit()
            else:
                return True

        columns_check(df, columns)
        strategies = {col: columns[col].split(';') for col in columns}

        for strategy in strategies:
            df['{}_benefits'.format(strategy)] = df['reduction_costs_{}'.format(strategy)] * costs_dict['npv_factor']
            select_col = strategies[strategy]
            if len(select_col) == 1:
                df['{}_costs'.format(strategy)] = df[select_col[0]] * costs[strategy] * -1 / 1000
            if len(select_col) > 1:
                df['{}_costs'.format(strategy)] = (df[select_col[0]] - df[select_col[1]]) * costs[strategy] * -1 / 1000
                df['{}_costs'.format(strategy)] = df['{}_costs'.format(strategy)].where(df['{}_costs'.format(strategy)] > 1, other=np.nan)
            df['{}_bc_ratio'.format(strategy)] = df['{}_benefits'.format(strategy)] / df['{}_costs'.format(strategy)]

        return df


class RoadDamage:
    def calculate_direct_damage(self, road_gdf):
        """
        Calculates the direct damage for all road segments with exposure data using a depth-damage curve
        Arguments:
            *road_gdf* (GeoPandas DataFrame) :
        Returns:
            *road_gdf* (GeoPandas DataFrame) :
        """

        # apply the add_default_lanes function to add default number of lanes
        # load lookup tables
        # These factors are derived from: Van Ginkel et al. 2021: https://nhess.copernicus.org/articles/21/1011/2021/
        logging.warning('Damage calculations are based on Van Ginkel et al. 2021: https://nhess.copernicus.org/articles/21/1011/2021/')
        logging.warning("""All damages represent the former EU-28 (before Brexit), 2015-pricelevel in Euro's.
                            To convert to local currency, these need to be:
                                multiplied by the ratio (pricelevel_XXXX / pricelevel_2015)
                                multiply by the ratio (local_GDP_per_capita / EU-28-2015-GDP_per_capita)          
                            EU-28-2015-GDP_per_capita = 39.200 euro
                        """)
        logging.warning("These numbers assume that motorways that each driving direction is mapped as a seperate segment such as in OSM!!!")
        lane_damage_correction = lookup.road_damage_correction()
        dict_max_damages = lookup.max_damages() #In fact this is a new construction costs
        max_damages_huizinga = lookup.max_damages_huizinga()
        interpolators = lookup.flood_curves() #input: water depth (cm); output: damage (fraction road construction costs)
        curve_names = [name for name in interpolators]

        #Find the hazard columns
        val_cols = [col for col in road_gdf.columns if (col[0].isupper() and col[1] == '_')]

        #group the val cols:
        # Todo: make a hazard class?
        # For now: this is how we do the hazard bookkeeping:
        # F_EV1_ma
        # F = flood; _ ; EV = event-based + number event; _ ; _ ma/mi/mi/av/fr = maximum, minimum, average fraction that is affected

        #case we are dealing with events:
        event_cols = [x for x in val_cols if '_EV' in x]
        rp_cols = [x for x in val_cols if '_RP' in x] #todo test the workflow for event data
        if len(event_cols) > 0 and len(rp_cols) == 0:
            #only event data is provided
            #unique_events = set([x.split('_')[1] for x in event_cols]) #set of unique events
            #hazard_stats = set([x.split('_')[2] for x in event_cols]) #set of hazard info per event

            event_gdf = event_hazard_network_gdf(road_gdf,val_cols)
            event_gdf.calculate_damage_HZ(interpolators['HZ'],max_damages_huizinga)
            #event_gdf.calculate_damage_OSdaMage(interpolators,dict_max_damages)

        #case we are dealing with return period
        elif len(rp_cols) > 0 and len(event_cols) == 0:
            #only return period data is provided
            print('RP data not yet implemented')
        else:
            raise ValueError(""""The hazard calculation does not know 
            what to do if {} event_cols and {} rp_cols are provided""".format(
                                len(event_cols),len(rp_cols)))

        return event_gdf.gdf

    @staticmethod
    def apply_lane_damage_correction(lane_damage_correction, road_type, lanes):
        """See load_lane_damage_correction; this function only avoids malbehaviour for weird lane numbers"""
        if lanes < 1:  # if smaller than the mapped value -> correct with minimum value
            lanes = 1
        if lanes > 6:  # if larger than largest mapped value -> use maximum value (i.e. 6 lanes)
            lanes = 6
        return lane_damage_correction[road_type][lanes]

    @staticmethod
    def apply_huizinga_max_dam(max_damages_huizinga, road_type, lanes):
        """See load_lane_damage_correction; this function only avoids malbehaviour for weird lane numbers"""
        if lanes < 1:  # if smaller than the mapped value -> correct with minimum value
            lanes = 1
        if lanes > 6:  # if larger than largest mapped value -> use maximum value (i.e. 6 lanes)
            lanes = 6
        return max_damages_huizinga[road_type][lanes]

    @staticmethod
    def apply_cleanup(x):
        """ Cleanup for entries in dataframe, where there is a list with two values for a single field.

         This happens when there is both a primary_link and a primary infra_type.
         x[0] indicates the values of the primary_link infra_type
         x[1] indicates the values of the primary infra_type
         """
        if x is None:
            return None
        if type(x) == list:
            return x[1]  # 1 means select primary infra_type
        else:
            return x


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
    gdf.crs = 'epsg:4326'  # TODO: decide if this should be variable with e.g. an output_crs configured

    for col in gdf.columns:
        if gdf[col].dtype == np_object and col != gdf.geometry.name:
            gdf[col] = gdf[col].astype(str)

    gdf.to_file(save_path, driver='ESRI Shapefile', encoding='utf-8')
    logging.info("Results saved to: {}".format(save_path))

class event_hazard_network_gdf():
    """A road network gdf with hazard data per event stored in it.

    Mandatory attributes:
        *self.events* (set)  : all available unique events
        *self.stats* (set)   : the available statistics
    """

    #Todo check how you can built this on top of geopandas df
    def __init__(self,road_gdf,val_cols):
        """Construct the network gdf and make some handy attributes
        """
        #todo self.hazard name
        self.val_cols = val_cols
        self.events = set([x.split('_')[1] for x in val_cols])  # set of unique events
        self.stats = set([x.split('_')[2] for x in val_cols])  # set of hazard info per event
        self.gdf = road_gdf

    def create_mask(self):
        """
        #Create a mask of only the dataframes with hazard data (to speed-up damage calculations)
        effect: *self.gdf_mask* = mask of only the rows with hazard data
        also returns this value
        """
        #because the fractions are often 0 (also if the rest is nan, this messes up the .isna)
        val_cols_temp = [c for c in self.val_cols if '_fr' not in c]

        gdf_mask = self.gdf.loc[~(self.gdf[val_cols_temp].isna()).all(axis=1)]
        self.gdf_mask = gdf_mask #todo: not sure if we need to store the mask
        return gdf_mask

    def calculate_damage_HZ(self,interpolator,max_damages_huizinga,curve_name = 'HZ'):
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
        assert 'me' in self.stats #mean water depth should be provided #todo if the mean is calculated over the whole or only inundated segment
        assert 'fr' in self.stats #the inundated fraction of the segment should be provided

        #Variable settings (not yet arguments)
        # Todo: Dirty fixes:
        hazard_prefix = 'F'
        end = 'me'  #indicate that you want to use the mean

        gdf_mask = self.create_mask()
        # create dataframe from gdf
        column_names = list(gdf_mask.columns)
        column_names.remove('geometry')
        df = gdf_mask[column_names]

        # fixing lanes #todo move out this function
        df['lanes_copy'] = df['lanes'].copy()
        df['lanes'] = df['lanes_copy'].where(df['lanes_copy'].astype(float) >= 1.0, other=1.0)
        df['lanes'] = df['lanes_copy'].where(df['lanes_copy'].astype(float) <= 6.0, other=6.0)

        df_max_damages_huizinga = pd.DataFrame.from_dict(max_damages_huizinga)
        df['max_dam_hz'] = df_max_damages_huizinga.lookup(df['lanes'], df['road_type'])

        for event in self.events: #todo self
            df['dam_{}_{}'.format(event,curve_name)] = round(
                   df['max_dam_hz'].astype(float)                                             #max damage (euro/km)
                 * interpolator(df['{}_{}_{}'.format(hazard_prefix,event,end)]).astype(float) #damage curve  (-)
                 * df['{}_{}_{}'.format(hazard_prefix,event,'fr')].astype(float)              #inundated fraction (-)
                 * df['length'], 2)                                                           #length segment (m)

        #Todo: still need to check the units
        logging.warning("Damage calculation units have not been checked!!! TODO")

        #Add the new columns add the right location to the df
        dam_cols = [c for c in df.columns if c.startswith('dam_')]
        self.gdf[dam_cols] = df[dam_cols]
        logging.info('calculate_damage_HZ(): Damage calculation with the Huizinga damage functions was succesfull')

    def calculate_damage_OSdaMage(self, interpolators, max_damages):
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
        assert 'me' in self.stats  # mean water depth should be provided #todo if the mean is calculated over the whole or only inundated segment
        assert 'fr' in self.stats  # the inundated fraction of the segment should be provided

        # Variable settings (not yet arguments)
        # Todo: Dirty fixes:
        hazard_prefix = 'F'
        end = 'me'  # indicate that you want to use the mean

        interpolators.pop('HZ', None)  # drop the Huizinga interpolator if for some reason it is still around

        gdf_mask = self.create_mask()
        # create dataframe from gdf
        column_names = list(gdf_mask.columns)
        column_names.remove('geometry')
        df = gdf_mask[column_names]

        # fixing lanes #todo move out this function
        df['lanes_copy'] = df['lanes'].copy()
        df['lanes'] = df['lanes_copy'].where(df['lanes_copy'].astype(float) >= 1.0, other=1.0)
        df['lanes'] = df['lanes_copy'].where(df['lanes_copy'].astype(float) <= 6.0, other=6.0)
        df['tuple'] = [tuple([0] * 5)] * len(df['lanes'])

        # CALCULATE MINIMUM AND MAXIMUM CONSTRUCTION COST PER ROAD TYPE
        # pre-calculation of max damages per percentage (same for each C1-C6 category)
        df['lower_damage'] = df['road_type'].copy().map(max_damages["Lower"]) #i.e. min construction costs
        df['upper_damage'] = df['road_type'].copy().map(max_damages["Upper"]) #i.e. max construction costs

        # create separate column for each percentile of construction costs (is faster then tuple)
        for percentage in [0, 25, 50, 75, 100]: #So this interpolates the min to the max damage
            df['damage_{}'.format(percentage)] = (df['upper_damage'] * percentage / 100) + (
                        df['lower_damage'] * (100 - percentage) / 100)

        columns = []
        for curve_name, interpolator in interpolators.items():
            #print(curve_name, interpolator)
            for event in self.events:
                for percentage in [0, 25, 50, 75, 100]:
                    df['dam_{}_{}_{}'.format(percentage,curve_name,event)] = round(
                          df['damage_{}'.format(percentage)].astype(float)                    #max damage (in euro/km)
                        * interpolator(df['{}_{}_{}'.format(hazard_prefix,event,end)]).astype(float) #damage curve: fraction f(depth-cm) #Todo check units
                        * df['{}_{}_{}'.format(hazard_prefix,event,'fr')].astype(float)     #inundated fraction of the segment
                        * df['length'].astype(float),2)                                     #total segment length (m)

                #This wraps it all in tuple again
                df['dam_{}_{}'.format(curve_name, event)] = tuple(zip(df['dam_0_{}_{}'.format(curve_name, event)],
                                                                      df['dam_25_{}_{}'.format(curve_name, event)],
                                                                      df['dam_50_{}_{}'.format(curve_name, event)],
                                                                      df['dam_75_{}_{}'.format(curve_name, event)],
                                                                      df['dam_100_{}_{}'.format(curve_name, event)]))

                #And throw way all intermediate results (that are not in the tuple)
                df = df.drop(columns=['dam_{}_{}_{}'.format(percentage,curve_name,event) for percentage in
                                      [0, 25, 50, 75, 100]])

        df = df.drop(columns=[c for c in df.columns if c.startswith('damage_')])

        #drop invalid combinations of damage curves and road types (C1-C4 for motorways; C5,C6 for other)
        all_dam_cols = [c for c in df.columns if c.startswith('dam_')]
        motorway_curves = [c for c in all_dam_cols if int(c.split('_')[1][-1]) <= 4] #C1-C4
        other_curves = [c for c in all_dam_cols if int(c.split('_')[1][-1]) > 4] #C5, C6

        for curve in other_curves:
            df.loc[df['road_type'] == ('motorway' or 'trunk'),curve] = np.nan

        for curve in motorway_curves:
            df.loc[df['road_type'] != ('motorway' or 'trunk'), curve] = np.nan

        # Todo: still need to check the units
        logging.warning("Damage calculation units have not been checked!!! TODO")

        # Add the new columns add the right location to the df
        self.gdf[all_dam_cols] = df[all_dam_cols]
        logging.info('calculate_damage_OSdaMage(): Damage calculation with the OSdaMage functions was succesfull')






