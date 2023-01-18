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
        *self.return_periods* (set of strings): 'e.g
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
        _to_integrate = _to_integrate.sort_index(axis='columns', ascending=False)  # from large to small RP

        if mode == 'default':

            _to_integrate = self.rework_damage_data_default(_to_integrate)
            _risk = self.integrate_df_trapezoidal(_to_integrate.copy())
            self.gdf['risk'] = _risk

        elif mode.startswith('cut_from'):
            """
            In this mode, the integration mimics the presence of a flood protection
            """
            _cutoff_rp = int(mode.split('_')[2])

            _rps = list(_to_integrate.columns)

            if _cutoff_rp <= min(_rps):
                raise ValueError("""
                RA2CE cannot calculate risk in 'cut_from' mode if 
                Return period of the cutoff ({}) <= smallest available return period ({})
                Use 'default' mode or 'triangle_to_null_mode' instead.
                                    """.format(_cutoff_rp,min(_rps)))

            elif min(_rps) < _cutoff_rp < max(_rps): #if protection level is between min and max RP
                _to_integrate = self.rework_damage_data_cut_from(_to_integrate, _cutoff_rp)
                _risk = self.integrate_df_trapezoidal(_to_integrate.copy())

            elif _cutoff_rp >= max(_rps): #cutoff is larger or equal than largest return period
                # risk is return frequency of cutoff
                # times the damage of the most extreme event
                _to_integrate = _to_integrate.fillna(0)
                _risk = _to_integrate[_rps[0]]/_cutoff_rp
                _max_RP = max(_to_integrate.columns)

            self.gdf['risk'] = _risk

        elif mode.startswith('triangle_to_null'):
            """
            In this mode, an extra data point with zero damage is added at some distance from the smallest known RP,
            and the area of the Triangle this creates is also calculated
            """

            _rps = list(_to_integrate.columns)

            _triangle_end = int(mode.split('_')[3]) #The return period at which the triangle should end

            if _triangle_end >= min(_rps):
                raise ValueError("""
                RA2CE cannot calculate risk in 'triangle_to_null' mode if 
                Return period of the triangle ({}) >= smallest available return period ({})
                Use 'default' mode or 'cut_from' instead.
                                    """.format(_triangle_end,min(_rps)))

            _to_integrate = self.rework_damage_data_triangle_to_null(_to_integrate, _triangle_end)
            _risk = self.integrate_df_trapezoidal(_to_integrate.copy())

            self.gdf['risk'] = _risk




    def verify_damage_data_for_risk_calculation(self):
        """
        Do some data quality and requirement checks before starting the risk calculation

        :return:
        """
        #Check if there is only one unique damage function
        #RP should in the column name
        pass

    @staticmethod
    def integrate_df_trapezoidal(df: pd.DataFrame)-> np.array:
        """
        Arguments:
            *df* (pd.DataFrame) :
                Column names should contain return periods (years)
                Each row should contain a set of damages for one object

        Returns:
            np.array : integrated result per row

        """
        #convert return periods to frequencies
        df.columns = [1/RP for RP in df.columns]
        #sort columns by ascending frequency
        df = df.sort_index(axis='columns')
        values = df.values
        frequencies = df.columns
        return np.trapz(values,frequencies,axis=1)

    @staticmethod
    def rework_damage_data_default(_to_integrate: pd.DataFrame) -> pd.DataFrame:
        """
        Rework the damage data to make it suitable for integration (risk calculation) in default mode
        
        :param _to_integrate: 
        :return: _to_integrate
        """
        # Copy the maximum return period with an infinitely high damage
        _max_RP = max(_to_integrate.columns)
        _to_integrate[float('inf')] = _to_integrate[_max_RP]

        # Stop integrating at the last known return period, so no further manipulation needed
        _min_RP = min(_to_integrate.columns)

        _to_integrate = _to_integrate.fillna(0)

        logging.info("""Risk calculation runs in 'default' mode. 
                    Assumptions:
                        - for all return periods > max RP{}, damage = dam_RP{}
                        - for all return periods < min RP{}, damage = 0

                    """.format(_max_RP, _max_RP, _min_RP))
        return _to_integrate

    @staticmethod
    def rework_damage_data_cut_from(_to_integrate: pd.DataFrame, _cutoff_rp: float) -> pd.DataFrame:
        """
        Rework the damage data to make it suitable for integration (risk calculation) in default mode

        :param _to_integrate: 
                _cutoff_rp : the return period at which to make the cutoff, aka the flood protection level
        :return: _to_integrate
        """
        _rps = list(_to_integrate.columns)

        if _cutoff_rp in _rps:
            _dropcols = [rp for rp in _rps if rp < _cutoff_rp]
            _to_integrate = _to_integrate.drop(columns=_dropcols)
        else:
            pos = _rps.index(next(i for i in _rps if i < _cutoff_rp))  # find position of first RP value < PL
            # _to_integrate = _to_integrate[_rps[0:pos+1]] #remove all the values with smaller RPs than the PL

            _frequencies = _to_integrate.copy()
            _frequencies.columns = [1 / c for c in _frequencies.columns]

            _frequencies[1 / _cutoff_rp] = np.nan
            _frequencies = _frequencies.interpolate(method='index', axis=1)

            # Drop the columns outside the cutoff
            _dropcols = [c for c in _frequencies.columns if c > 1 / _cutoff_rp]
            _frequencies = _frequencies.drop(columns=_dropcols)

            _to_integrate = _frequencies
            _to_integrate.columns = [1 / c for c in _to_integrate.columns]

            # Copy the maximum return period with an infinitely high damage
            _max_RP = max(_to_integrate.columns)
            _to_integrate[float('inf')] = _to_integrate[_max_RP]

            _to_integrate = _to_integrate.fillna(0)

        logging.info("""Risk calculation runs in 'cut_from' mode. 
                                Assumptions:
                                    - for all return periods > max RP{}, damage = dam_RP{}
                                    - damage at cutoff is linearly interpolated from known damages
                                    - no damage for al RPs > RP_cutoff ({})

                                """.format(_max_RP, _max_RP, _cutoff_rp))

        return _to_integrate

    @staticmethod
    def rework_damage_data_triangle_to_null(_to_integrate: pd.DataFrame, _triangle_end: float) -> pd.DataFrame:
        """
        Rework the damage data to make it suitable for integration (risk calculation) in default mode

        :param _to_integrate:
                _triangle_end_rp : the return period at to end the triangle
        :return: _to_integrate
        """
        # Copy the maximum return period with an infinitely high damage
        _max_RP = max(_to_integrate.columns)
        _to_integrate[float('inf')] = _to_integrate[_max_RP]

        # At the return period of the triangle end, set all damage values to zero
        _to_integrate[_triangle_end] = 0

        _to_integrate = _to_integrate.sort_index(axis='columns', ascending=False)  # from large to small RP

        _to_integrate = _to_integrate.fillna(0)

        logging.info("""Risk calculation runs in 'triangle to null' mode. 
                                Assumptions:
                                    - for all return periods > max RP{}, damage = dam_RP{}
                                    - at the end of the triangle {}, damage = 0

                                """.format(_max_RP, _max_RP, _triangle_end))
        return _to_integrate


def test_integrate_df_trapezoidal():
    data = np.array(([[1000,2000],[500,1000]]))
    rps = [100,200]

    df = pd.DataFrame(data,columns=rps)
    res = integrate_df_trapezoidal(df)

    assert res == np.array([7.5,3.75])


def test_construct_damage_network_return_periods():
    data_path= Path(r'D:\Python\ra2ce\tests\analyses\direct\test_data\risk_test_data.csv')
    damage_network = DamageNetworkReturnPeriods.construct_from_csv(data_path,sep=';')
    assert type(damage_network) == DamageNetworkReturnPeriods, 'Did not construct object of the right type'

def test_risk_calculation_default():
    data_path = Path(r'D:\Python\ra2ce\tests\analyses\direct\test_data\risk_test_data.csv')
    damage_network = DamageNetworkReturnPeriods.construct_from_csv(data_path, sep=';')
    damage_network.control_risk_calculation(mode='default')
    assert damage_network.gdf['risk'][0] == damage_network.gdf['ref_risk_default'][0]

def test_risk_calculation_cutoff():
    data_path = Path(r'D:\Python\ra2ce\tests\analyses\direct\test_data\risk_test_data.csv')
    for rp in [15,200,25]:
        damage_network = DamageNetworkReturnPeriods.construct_from_csv(data_path, sep=';')
        damage_network.control_risk_calculation(mode='cut_from_{}_year'.format(rp))
        test_result = round(damage_network.gdf['risk'][0],0)
        reference_result = round(damage_network.gdf['ref_risk_cut_from_{}_year'.format(rp)][0],0)
        assert test_result == reference_result

def test_risk_calculation_triangle_to_null():
    data_path = Path(r'D:\Python\ra2ce\tests\analyses\direct\test_data\risk_test_data.csv')
    damage_network = DamageNetworkReturnPeriods.construct_from_csv(data_path, sep=';')
    for triangle_rp in [8,2]:
        damage_network.control_risk_calculation(mode='triangle_to_null_{}_year'.format(triangle_rp))
        test_result = round(damage_network.gdf['risk'][0], 0)
        reference_result = round(damage_network.gdf['ref_risk_triangle_to_null_{}_year'.format(triangle_rp)][0], 0)
        assert test_result == reference_result



if __name__ == "__main__":
    test_construct_damage_network_return_periods()
    test_risk_calculation_default()
    test_risk_calculation_cutoff()
    test_risk_calculation_triangle_to_null()
