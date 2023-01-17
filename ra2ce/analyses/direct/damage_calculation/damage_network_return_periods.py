import logging

from ra2ce.analyses.direct.damage_calculation.damage_network_base import (
    DamageNetworkBase,
)

import numpy as np
import pandas as pd
from pathlib import Path


class DamageNetworkReturnPeriods(DamageNetworkBase):
    """
    A road network gdf with Return-Period based hazard data stored in it,
    and for which damages and risk can be calculated
    @Author: Kees van Ginkel

    Mandatory attributes:
        *self.rps* (set)  : all available unique events
        *self.stats* (set)   : the available statistics
    """

    def __init__(self, road_gdf, val_cols):
        # Construct using the parent class __init__
        super().__init__(road_gdf, val_cols)

        self.return_periods = set(
            [x.split("_")[1] for x in val_cols]
        )  # set of unique return_periods

        if not len(self.return_periods) > 1:
            raise ValueError("No return_period cols present in hazard data")

    @classmethod
    def construct_from_csv(cls,path,sep=';'):
        road_gdf = pd.read_csv(path,sep=sep)
        val_cols = [c for c in road_gdf.columns if c.startswith('F_')] #Find everything starting with 'F'
        return cls(road_gdf,val_cols)

    ### Controlers for return period based damage and risk calculations
    def main(self, damage_function, manual_damage_functions):
        """
        Control the damage calculation per return period

        """

        assert len(self.return_periods) > 0, "no return periods identified"
        assert "me" in self.stats, "mean water depth (key: me) is missing"
        assert "fr" in self.stats, "inundated fraction (key: fr) is missing"

        self.do_cleanup_and_mask_creation()

        if damage_function == "HZ":
            self.calculate_damage_HZ(events=self.return_periods)

        if damage_function == "OSD":
            self.calculate_damage_OSdaMage(events=self.return_periods)

        if damage_function == "MAN":
            self.calculate_damage_manual_functions(
                events=self.events, manual_damage_functions=manual_damage_functions
            )

    def control_risk_calculation(self,mode='default'):
        """
        Controler of the risk calculation, which calls the correct risk (integration) functions

        Arguments:
            *mode* (string) : the sort of risk calculation that you want to do, can be:
                                ‘default’, 'cut_from_YYYY_year’, ‘triangle_to_null_YYYY_year’
        """
        self.verify_damage_data_for_risk_calculation()

        # prepare the parameters of the risk calculation
        dam_cols = [c for c in self.gdf.columns if c.startswith('dam')]
        _to_integrate = self.gdf[dam_cols]
        _to_integrate.columns = [float(c.split('_')[1].replace('RP', '')) for c in _to_integrate.columns]

        if mode == 'default':

            #Copy the maximum return period with an infinitely high damage
            _max_RP = max(_to_integrate.columns)
            _to_integrate[float('inf')] =_to_integrate[_max_RP]

            #Stop integrating at the last known return period, so no further manipulation needed
            _min_RP = min(_to_integrate.columns)

            _to_integrate = _to_integrate.fillna(0)

            _risk = integrate_df_trapezoidal(_to_integrate.copy())
            self.gdf['risk'] = _risk

            logging.info("""Risk calculation was succesfull, and ran in 'default' mode. 
            Assumptions:
                - for all return periods > max RP{}, damage = dam_RP{}
                - for all return periods < min RP{}, damage = 0
            
            """.format(_max_RP, _max_RP, _min_RP))


        elif mode.startswith('cut_from'):
            """
            In this mode, the integration mimics the presence of a flood protecit
            """
            _cutoff_rp = int(mode.split('_')[2])

            # Copy the maximum return period with an infinitely high damage
            _max_RP = max(_to_integrate.columns)
            _to_integrate[float('inf')] = _to_integrate[_max_RP]

            ###Todo: hier verder: iets met de eerste erboven, en de eerste eronder qua RP, dan inverse en dan inteproleren?
            

            #Drop all the columns with an RP below the cutoff (aka protection level)
            #_cols_to_drop = [c for c in _to_integrate.columns if c < _cutoff_rp]

            # F
            _min_RP = min(_to_integrate.columns)

            _to_integrate = _to_integrate.fillna(0)

            _risk = integrate_df_trapezoidal(_to_integrate.copy())
            self.gdf['risk'] = _risk

            logging.info("""Risk calculation was succesfull, and ran in 'default' mode. 
                        Assumptions:
                            - for all return periods > max RP{}, damage = dam_RP{}
                            - for all return periods < min RP{}, damage = 0

                        """.format(_max_RP, _max_RP, _min_RP))

            pass
        elif mode.startswith('triangle_to_null'):
            #This is the approach used in the Mozambique project
            pass

    def verify_damage_data_for_risk_calculation(self):
        """
        Do some data quality and requirement checks before starting the risk calculation

        :return:
        """
        #Check if there is only one unique damage function
        #RP should in the column name
        pass

    def calculate_expected_annual_damage(self):

        pass


def integrate_df_trapezoidal(df):
    """
    Column names should contain return periods (years)
    Each row should contain a set of damages for one object

    """
    #convert return periods to frequencies
    df.columns = [1/RP for RP in df.columns]
    #sort columns by ascending frequency
    df = df.sort_index(axis='columns')
    values = df.values
    frequencies = df.columns
    return np.trapz(values,frequencies,axis=1)

def test_integrate_df_trapezoidal():
    data = np.array(([[1000,2000],[500,1000]]))
    rps = [100,200]

    df = pd.DataFrame(data,columns=rps)
    res = integrate_df_trapezoidal(df)

    assert res == np.array([7.5,3.75])

def test_risk_calculation_default():
    pass

def test_construct_damage_network_return_periods():
    data_path= Path(r'D:\Python\ra2ce\tests\analyses\direct\test_data\test_data.csv')
    damage_network = DamageNetworkReturnPeriods.construct_from_csv(data_path,sep=';')
    pass

if __name__ == "__main__":
    test_construct_damage_network_return_periods()
    pass
