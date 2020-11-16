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

        self.results = pd.DataFrame(index=self.data.keys()) #Index = osm_id


    def calculate_area(self):
        """
        The road_hazard.results DataFrame has al the results that should be fed to the RA2CE tool.
        """

        df = self.results
        df['Pavement_area'] = None
        df['Pavement_perc_flooded'] = None
        df['Pavement_avg_depth'] = None
        df['Embankment_area'] = None
        df['Embankment_perc_flooded'] = None
        df['Embankment_avg_depth'] = None

        for osm_id,values in self.data.items():
            df.at[osm_id,'Embankment_area'] = values['1']['count'] * self.cellsize
            df.at[osm_id, 'Pavement_area'] = values['2']['count'] * self.cellsize
            df.at[osm_id, 'Pavement_perc_flooded'] = \
                100 * (len(values['2']['wd']) / values['2']['count'])
            df.at[osm_id, 'Pavement_avg_depth'] = np.mean((values['2']['wd']))











