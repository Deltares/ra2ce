#This module contains functionality for the direct analysis done for Rijkswaterstaat in November/December 2020
#It assumes that the hazard data is already assigned to the OSM segments using a grid-based appraoch (DELFT-FIAT)
#@Author: Kees van Ginkel

from pathlib import Path
import json
import pandas as pd
import numpy as np
import pathlib

class road_hazard():
    """
    A road_hazard object is an OSM-road segment, containing flood hazard data calculated with Delft-FIAT.
    It is instantiated from a .json file deliverd by Dennis.
    @author: Kees van Ginkel
    """

    def __init__(self,json_path,cellsize):
        """
        Initiate a road_hazard object from an .json file
        Key 0 indicates that the ground is property of RWS, but not embankment or road pavement
        Key 1 indicates embankment
        Key 2 indicates road pavement

        Arguments:
            *json_path* (Path) : Path to the json file
            *cellsize* (float) : Cellsize of gridcells in m^2 (e.g. 25 m2)

        Attributes:
            self.data (dict) : Containg the raw data from the json file
            self.results (df) : Containing the results that feed into RA2CE
            self.name (string) : Hazard name, is derived from the filename

        """
        assert isinstance(json_path,pathlib.Path)
        self.name = json_path.stem
        self.cellsize = cellsize

        with open(json_path) as json_file:
            data = json.load(json_file)
        print('loaded {}'.format(json_path))
        self.data = data #Each key is osm_id

        self.results = pd.DataFrame(index = [int(key) for key in self.data.keys()]) #Index = osm_id
        self.osm_split_id = list(self.results.index)


    def calculate_area(self,underlying_network = False):
        """
        The road_hazard.results DataFrame has al the results that should be fed to the RA2CE tool.

        Arguments:
            *underlying_network* (Boolean) : Also calculate areas for roads not owned by RWS (default = False)
            # This was added as a kwarg to guarantee backward compatability

        Effect:
            Adds columns for pavement_*, Embankment_*, and optionally: Underlying_*
            ... *_area, *_perc_flooded, *_avg_depth, *max_depth
        """

        df = self.results
        df['Pavement_area'] = np.NaN
        df['Pavement_perc_flooded'] = np.NaN
        df['Pavement_avg_depth'] = np.NaN
        df['Pavement_max_depth'] = np.NaN
        df['Embankment_area'] = np.NaN
        df['Embankment_perc_flooded'] = np.NaN
        df['Embankment_avg_depth'] = np.NaN
        df['Embankment_max_depth'] = np.NaN

        if underlying_network:
            df['Underlying_area'] = np.NaN
            df['Underlying_perc_flooded'] = np.NaN
            df['Underlying_avg_depth'] = np.NaN
            df['Pavement_max_depth'] = np.NaN

        for osm_id,values in self.data.items():
            osm_id = int(osm_id)

            #Create results for embankments
            df.at[osm_id,'Embankment_area'] = values['1']['count'] * self.cellsize
            if values['1']['count'] != 0: #Has pixels with embanked area
                if len(values['1']['wd']) != 0: #Has flooded pixels
                    df.at[osm_id, 'Embankment_perc_flooded'] = \
                        100 * (len(values['1']['wd']) / values['1']['count'])
                    df.at[osm_id, 'Embankment_avg_depth'] = np.mean((values['1']['wd']))
                    df.at[osm_id, 'Embankment_max_depth'] = np.max((values['1']['wd']))
                else: #Has no flooded pixels
                    df.at[osm_id, 'Embankment_perc_flooded'] = 0
                    #other values will remain np.NaN

            #Create results for pavements
            df.at[osm_id, 'Pavement_area'] = values['2']['count'] * self.cellsize
            if values['2']['count'] != 0: #Has pixels with pavement
                if len(values['2']['wd']) != 0:  # Has flooded pixels
                    df.at[osm_id, 'Pavement_perc_flooded'] = \
                        100 * (len(values['2']['wd']) / values['2']['count'])
                    df.at[osm_id, 'Pavement_avg_depth'] = np.mean((values['2']['wd']))
                    df.at[osm_id, 'Pavement_max_depth'] = np.max((values['2']['wd']))
                else: #Has no flooded pixels
                    df.at[osm_id, 'Pavement_perc_flooded'] = 0
                    #other values will remain np.NaN

            if underlying_network: #Only execute if also information about non_RWS should be stored
                # Create results for RWS_network
                df.at[osm_id, 'Underlying_area'] = values['3']['count'] * self.cellsize
                if values['3']['count'] != 0:  # Has pixels with underlying network data
                    if len(values['3']['wd']) != 0:  # Has flooded pixels
                        df.at[osm_id, 'Underlying_perc_flooded'] = \
                            100 * (len(values['3']['wd']) / values['3']['count'])
                        df.at[osm_id, 'Underlying_avg_depth'] = np.mean((values['3']['wd']))
                        df.at[osm_id, 'Underlying_max_depth'] = np.max((values['3']['wd']))
                    else:  # Has no flooded pixels
                        df.at[osm_id, 'Underlying_perc_flooded'] = 0
                        # other values will remain np.NaN

    def OSdaMage_test(self):
        "Prepare some sample data for the OSdaMage code (now in ra2ce)"
        ### TODO

def RWS_blend(r,correction_factor=1.72):
    """
    Blends from the default OSdaMage functions according to the memo
    Note that at this stage, the OSdaMage functions have already been translated and are only calculated for pavements

    Args:
        *r* (road segment) -- a row from the merged results dataframe;
                should have columns dam_C1_01, ..C2.., C3, C4, C5, C5 and HZ
        *correction_factor (float) -- correction factor for inflation and NL-pricelevel

    Returns:
        *r* (road segment) -- the road segment with some new columns
    """

  #Drop columns C3 and C4, who apply on simple road designs

  # MIX THE MOST FITTING MAXIMUM DAMAGE
    if r['road_type'] in ['motorway', 'trunk']:
      r['low_flow_50'] = r['dam_C1_01'][2]
      r['low_flow_75'] = r['dam_C1_01'][3]
      r['low_flow_100'] = r['dam_C1_01'][4]
      r['high_flow_50'] = r['dam_C2_01'][2]
      r['high_flow_75'] = r['dam_C2_01'][3]
      r['high_flow_100'] = r['dam_C2_01'][4]

    elif r['road_type'] in ['primary', 'secondary','tertiary']:
      r['low_flow_50'] = r['dam_C5_01'][2]
      r['low_flow_75'] = r['dam_C5_01'][3]
      r['low_flow_100'] = r['dam_C5_01'][4]
      r['high_flow_50'] = r['dam_C6_01'][2]
      r['high_flow_75'] = r['dam_C6_01'][3]
      r['high_flow_100'] = r['dam_C6_01'][4]

    r['HZ_corr'] = r['dam_HZ_01']

    #select columns to correct values for
    to_correct = ['low_flow_50', 'low_flow_75', 'low_flow_100',
       'high_flow_50', 'high_flow_75', 'high_flow_100','HZ_corr']

    for col in to_correct:
        r[col] = correction_factor * r[col]

    return r

def RWS_blend_sep_dam(r,correction_factor=1.72):
    """
    Blends from the default OSdaMage functions with seperate damage functions for pavements and embankments
    Water depth on embankments are HAZARD 1, for which damage curves C3 and C4 are applicable
    Water depth on pavements are the HAZARD 2, for which damage curves C1 and C2 are applicable

    Note that this is to be combined with the appropriate RA2CE configuration with seperate damage functions!!!!

    Args:
        *r* (road segment) -- a row from the merged results dataframe;
                should have columns dam_C1_01, ..C2.., C3, C4, C5, C5 and HZ
        *correction_factor (float) -- correction factor for inflation and NL-pricelevel

    Returns:
        *r* (road segment) -- the road segment with some new columns
    """

  #Drop columns C3 and C4, who apply on simple road designs

  # MIX THE MOST FITTING MAXIMUM DAMAGE
    if r['road_type'] in ['motorway', 'trunk']:
      r['EM_lf_50'] = r['dam_C3_01'][2]
      r['EM_lf_75'] = r['dam_C3_01'][3]
      r['EM_lf_100'] = r['dam_C3_01'][4]
      r['EM_hf_50'] = r['dam_C4_01'][2]
      r['EM_hf_75'] = r['dam_C4_01'][3]
      r['EM_hf_100'] = r['dam_C4_01'][4]
      r['PV_lf_50'] = r['dam_C1_02'][2]
      r['PV_lf_75'] = r['dam_C1_02'][3]
      r['PV_lf_100'] = r['dam_C1_02'][4]
      r['PV_hf_50'] = r['dam_C2_02'][2]
      r['PV_hf_75'] = r['dam_C2_02'][3]
      r['PV_hf_100'] = r['dam_C2_02'][4]

    elif r['road_type'] in ['primary', 'secondary','tertiary']:
      r['lf_50'] = r['dam_C5_01'][2]
      r['lf_75'] = r['dam_C5_01'][3]
      r['lf_100'] = r['dam_C5_01'][4]
      r['hf_50'] = r['dam_C6_01'][2]
      r['hf_75'] = r['dam_C6_01'][3]
      r['hf_100'] = r['dam_C6_01'][4]

    r['HZ_corr'] = r['dam_HZ_01']

    #select columns to correct values for
    to_correct = []
    for a in ['EM', 'PV']:
        for b in ['lf', 'hf']:
            for c in ['50', '75', '100']:
                to_correct.append("{}_{}_{}".format(a, b, c))

    for b in ['lf', 'hf']:
        for c in ['50', '75', '100']:
            to_correct.append("{}_{}".format(b, c))

    to_correct.append('HZ_corr')

    for col in to_correct:
        if col in r:
            r[col] = correction_factor * r[col]

    return r











