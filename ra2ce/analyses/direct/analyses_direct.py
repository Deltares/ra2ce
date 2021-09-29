# -*- coding: utf-8 -*-
"""
Created on 26-7-2021
@author: F.C. de Groen, Deltares
"""

import geopandas as gpd
import logging
import time
from .direct_lookup import LookUp as lookup
import numpy as np
import pandas as pd
import os, sys
from numpy import object as np_object


folder = os.path.dirname(os.path.realpath(__file__))
sys.path.append(folder)


class DirectAnalyses:
    def __init__(self, config, graphs):
        self.config = config
        self.graphs = graphs

    def road_damage(self, analysis):
        rd = RoadDamage()
        gdf = self.graphs['base_network_hazard']
        if self.graphs['base_network_hazard'] is None:
            gdf = gpd.read_feather(self.config['files']['base_network_hazard'])

        # TODO: This should probably not be done here, but at the create network function
        # apply road mapping to fewer types
        road_mapping_dict = lookup.road_mapping()
        gdf.rename(columns={'highway': 'infra_type'}, inplace=True)
        gdf['road_type'] = gdf['infra_type']
        gdf = gdf.replace({"road_type": road_mapping_dict})

        # TODO sometimes there are edges with multiple mappings
        # cleanup of gdf
        for column in gdf.columns:
            gdf[column] = gdf[column].apply(rd.apply_cleanup)

        gdf.loc[gdf.lanes == 'nan', 'lanes'] = np.nan  # replace string nans with numpy nans
        gdf.lanes = gdf.lanes.astype('float')  # convert strings to floats (not int, because int cant have nan)

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
        df_cba = df_cba.drop(columns=['dichtbij', 'ver_hoger', 'hwa_afw_ho', 'gw_hwa', 'slope_0015', 'slope_001',
                                      'return_period', 'event_length', 'event_costs'])
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
            *road_gdf* () :
        """

        # apply the add_default_lanes function to add default number of lanes
        default_lanes_dict = lookup.road_lanes()
        df_lookup = pd.DataFrame.from_dict(default_lanes_dict)

        road_gdf['country'] = 'NL'
        road_gdf['default_lanes'] = df_lookup.lookup(road_gdf['road_type'], road_gdf['country'])
        road_gdf['lanes'].fillna(road_gdf['default_lanes'], inplace=True)
        road_gdf = road_gdf.drop(columns=['default_lanes', 'country'])
        # road_gdf.lanes = road_gdf.apply(lambda x: default_lanes_dict[country][x['road_type']] if pd.isnull(x['lanes']) else x['lanes'],
        #                           axis=1).copy()

        # load lookup tables
        lane_damage_correction = lookup.road_damage_correction()
        dict_max_damages = lookup.max_damages()
        max_damages_huizinga = lookup.max_damages_huizinga()
        interpolators = lookup.flood_curves()

        # Perform loss calculation for all road segments
        val_cols = [x for x in list(road_gdf.columns) if 'val' in x]

        # Remove all rows from the dataframe containing roads that don't intersect with floods
        df = road_gdf.loc[~(road_gdf[val_cols] == 0).all(axis=1)]
        hzd_names = [i.split('val_')[1] for i in val_cols]

        curve_names = [name for name in interpolators]

        # TODO: remove the old calculation, it is redundant, but still in the code for reference.
        use_old_calculation = False
        if use_old_calculation is True:
            for curve_name in interpolators:
                interpolator = interpolators[curve_name]  # select the right interpolator
                from tqdm import tqdm
                tqdm.pandas(desc=curve_name)
                df = df.progress_apply(lambda x: self.road_loss_estimation(x,   interpolator, hzd_names, dict_max_damages,
                                                                           max_damages_huizinga, curve_name, lane_damage_correction),
                                       axis=1)

        else:
            # This calculation is 60 times faster:
            df = self.road_loss_estimation2(df, interpolators, hzd_names, dict_max_damages,
                                            max_damages_huizinga, curve_names, lane_damage_correction)

        return df

    def road_loss_estimation(self, x, interpolator, events, max_damages, max_damages_HZ, curve_name, lane_damage_correction,
                             **kwargs):
        """
        Carries out the damage estimation for a road segment using various damage curves

        Arguments:
            *x* (Geopandas Series) -- a row from the region GeoDataFrame with all road segments
            *interpolator* (SciPy interpolator object) -- the interpolator function that belongs to the damage curve
            *events* (List of strings) -- containing the names of the events: e.g. [rp10,...,rp500]
                scripts expects that x has the columns length_{events} and val_{events} which it needs to do the computation
            *max_damages* (dictionary) -- dictionary containing the max_damages per road-type; not yet corrected for the number of lanes
            *max_damages_HZ* (dictionary) -- dictionary containing the max_damages per road-type and number of lanes, for the Huizinga damage curves specifically
            *name_interpolator* (string) -- name of the max_damage dictionary; to save as column names in the output pandas DataFrame -> becomes the name of the interpolator = damage curve
            *lane_damage_correction (OrderedDict) -- the max_dam correction factors (see load_lane_damage_correction)

        Returns:
            *x* (GeoPandas Series) -- the input row, but with new elements: the waterdepths and inundated lengths per RP, and associated damages for different damage curves

        """

        #try:
        if True:
            # GET THE EVENT-INDEPENDENT METADATA FROM X
            road_type = x["road_type"]  # get the right road_type to lookup ...

            # abort the script for not-matching combinations of road_types and damage curves
            if ((road_type in ['motorway', 'trunk'] and curve_name not in ["C1", "C2", "C3", "C4", "HZ"]) or
                (road_type not in ['motorway', 'trunk'] and curve_name not in ["C5", "C6",
                                                                               "HZ"])):  # if combination is not applicable
                for event in events:  # generate (0,0,0,0,0) output for each event
                    x["dam_{}_{}".format(curve_name, event)] = tuple([0] * 5)
                return x

            lanes = x["lanes"]  # ... and the right number of lanes

            # DO THE HUIZINGA COMPARISON CALCULATION
            if curve_name == "HZ":  # only for Huizinga
                # load max damages huizinga
                max_damage = self.apply_huizinga_max_dam(max_damages_HZ, road_type, lanes)  # dict lookup: [road_type][lanes]
                for event in events:
                    depth = x["val_{}".format(event)]
                    length = x["length_{}".format(event)]  # inundated length in km
                    x["dam_{}_{}".format(curve_name, event)] = round(max_damage * interpolator(depth) * length, 2)

            # DO THE MAIN COMPUTATION FOR ALL THE OTHER CURVES
            else:  # all the other curves
                # LOWER AN UPPER DAMAGE ESTIMATE FOR THIS ROAD TYPE BEFORE LANE CORRECTION
                lower = max_damages["Lower"][road_type]  # ... the corresponding lower max damage estimate ...
                upper = max_damages["Upper"][road_type]  # ... and the upper max damage estimate

                # CORRECT THE MAXIMUM DAMAGE BASED ON NUMBER OF LANES
                lower = lower * self.apply_lane_damage_correction(lane_damage_correction, road_type, lanes)
                upper = upper * self.apply_lane_damage_correction(lane_damage_correction, road_type, lanes)

                max_damages_interpolated = [lower, (3 * lower + upper) / 4, (lower + upper) / 2, (lower + 3 * upper) / 4,
                                            upper]  # interpolate between upper and lower: upper, 25%, 50%, 75% and higher
                # if you change this, don't forget to change the length of the exception output as well!
                for event in events:
                    depth = x["val_{}".format(event)]  # average water depth in cm
                    length = x["length_{}".format(event)]  # inundated length in km

                    results = [None] * len(
                        max_damages_interpolated)  # create empty list, which will later be coverted to a tuple
                    for index, key in enumerate(max_damages_interpolated):  # loop over all different damage functions;
                        # the key are the max_damage percentile
                        results[index] = round(interpolator(depth) * key * length,
                                               2)  # calculate damage using interpolator and round to eurocents
                    x["dam_{}_{}".format(curve_name, event)] = tuple(results)  # save results as a new column to series x

        return x

    @staticmethod
    def road_loss_estimation2(gdf, interpolators, events, max_damages, max_damages_huizinga, curve_names, lane_damage_correction):
        """
        Carries out the damage estimation for a road segment using various damage curves

        Arguments:
            *gdf* (Geopandas Series) -- a row from the region GeoDataFrame with all road segments
            *interpolators* (SciPy interpolator object) -- the interpolator function that belongs to the damage curve
            *events* (List of strings) -- containing the names of the events: e.g. [rp10,...,rp500]
                scripts expects that x has the columns length_{events} and val_{events} which it needs to do the computation
            *max_damages* (dictionary) -- dictionary containing the max_damages per road-type; not yet corrected for the number of lanes
            *max_damages_HZ* (dictionary) -- dictionary containing the max_damages per road-type and number of lanes, for the Huizinga
                                            damage curves specifically
            *name_interpolator* (string) -- name of the max_damage dictionary; to save as column names in the output pandas DataFrame ->
                                            becomes the name of the interpolator = damage curve
            *lane_damage_correction (OrderedDict) -- the max_dam correction factors (see load_lane_damage_correction)

        Returns:
            *x* (GeoPandas Series) -- the input row, but with new elements: the waterdepths and inundated lengths per RP, and
                                        associated damages for different damage curves

        """
        # create dataframe from gdf
        column_names = list(gdf.columns)
        column_names.remove('geometry')
        df = gdf[column_names]

        # fixing lanes
        df['lanes_copy'] = df['lanes'].copy()
        df['lanes'] = df['lanes_copy'].where(df['lanes_copy'].astype(float) >= 1.0, other=1.0)
        df['lanes'] = df['lanes_copy'].where(df['lanes_copy'].astype(float) <= 6.0, other=6.0)
        df['tuple'] = [tuple([0] * 5)] * len(df['lanes'])

        # pre-calculation of max damages per percentage (same for each C1-C6 category)
        df['lower_damage'] = df['road_type'].copy().map(max_damages["Lower"])
        df['upper_damage'] = df['road_type'].copy().map(max_damages["Upper"])

        df_lane_damage_correction = pd.DataFrame.from_dict(lane_damage_correction)
        df['lower_dam'] = df['lower_damage'] * df_lane_damage_correction.lookup(df['lanes'], df['road_type'])
        df['upper_dam'] = df['upper_damage'] * df_lane_damage_correction.lookup(df['lanes'], df['road_type'])
        # df['lower_dam'] = df.apply(lambda x: x.lower_damage * lane_damage_correction[x.road_type][x.lanes], axis=1)
        # df['upper_dam'] = df.apply(lambda x: x.upper_damage * lane_damage_correction[x.road_type][x.lanes], axis=1)

        # create separate column for each percentage (is faster then tuple)
        for percentage in [0, 25, 50, 75, 100]:
            df['damage_{}'.format(percentage)] = (df['upper_dam'] * percentage / 100) + (df['lower_dam'] * (100 - percentage) / 100)

        columns = []
        for curve_name in curve_names:
            for event in events:
                interpolator = interpolators[curve_name]
                if curve_name == 'HZ':

                    df_max_damages_huizinga = pd.DataFrame.from_dict(max_damages_huizinga)
                    df['max_dam_hz'] = df_max_damages_huizinga.lookup(df['lanes'], df['road_type'])
                    # df['max_dam_hz'] = df.apply(lambda x: max_damages_huizinga[x.road_type][x.lanes], axis=1)

                    df['dam_{}_{}'.format(curve_name, event)] = round(df['max_dam_hz'].astype(float)
                                                                      * interpolator(df['val_{}'.format(event)]).astype(float)
                                                                      * df['length_{}'.format(event)].astype(float), 2)
                else:
                    for percentage in [0, 25, 50, 75, 100]:
                        df['dam_{}_{}_{}'.format(percentage, curve_name, event)] = round(df['damage_{}'.format(percentage)].astype(float)
                                                                                         * interpolator(df['val_{}'.format(event)]).astype(float)
                                                                                         * df['length_{}'.format(event)].astype(float), 2)

                    df['dam_{}_{}'.format(curve_name, event)] = tuple(zip(df['dam_0_{}_{}'.format(curve_name, event)],
                                                                          df['dam_25_{}_{}'.format(curve_name, event)],
                                                                          df['dam_50_{}_{}'.format(curve_name, event)],
                                                                          df['dam_75_{}_{}'.format(curve_name, event)],
                                                                          df['dam_100_{}_{}'.format(curve_name, event)]))

                    df = df.drop(columns=['dam_{}_{}_{}'.format(percentage, curve_name, event) for percentage in [0, 25, 50, 75, 100]])

                # change back to 0's if the combination doesnt exist
                if curve_name in ["C1", "C2", "C3", "C4"]:
                    # first copy values with trunk to temp column. Then replace everywhere
                    # except motorway with 0's, then copy files of trunk back
                    df.loc[df['road_type'] == 'trunk', 'temp'] = 'dam_{}_{}'.format(curve_name, event)
                    df.loc[df['road_type'] != 'motorway', 'dam_{}_{}'.format(curve_name, event)] = df['tuple']
                    df.loc[df['road_type'] == 'trunk', 'dam_{}_{}'.format(curve_name, event)] = df['temp']

                if curve_name in ["C5", "C6"]:
                    df.loc[df['road_type'] == 'motorway', 'dam_{}_{}'.format(curve_name, event)] = df['tuple']
                    df.loc[df['road_type'] == 'trunk', 'dam_{}_{}'.format(curve_name, event)] = df['tuple']

                columns.append('dam_{}_{}'.format(curve_name, event))

        gdf = pd.concat([gdf, df[columns]], axis=1)

        return gdf

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
