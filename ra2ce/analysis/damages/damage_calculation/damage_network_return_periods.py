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
from pathlib import Path

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.damages.damage_calculation.damage_network_base import (
    DamageNetworkBase,
)
from ra2ce.analysis.damages.shape_to_integrate_object.to_integrate_shaper_factory import (
    ToIntegrateShaperFactory,
)


class DamageNetworkReturnPeriods(DamageNetworkBase):
    """
    A road network gdf with Return-Period based hazard data stored in it,
    and for which damages and risk can be calculated
    @Author: Kees van Ginkel

    Mandatory attributes:
        *self.return_periods* (set of strings): 'e.g
        *self.stats* (set)   : the available statistics
    """

    def __init__(
        self,
        road_gdf: GeoDataFrame,
        val_cols: list[str],
        representative_damage_percentage: float,
    ):
        # Construct using the parent class __init__
        super().__init__(road_gdf, val_cols, representative_damage_percentage)

        self.return_periods = set(
            [x.split("_")[1] for x in val_cols]
        )  # set of unique return_periods

        if not any(self.return_periods):
            raise ValueError("No return_period cols present in hazard data")

    @classmethod
    def construct_from_csv(
        cls, csv_path: Path, representative_damage_percentage: float, sep: str
    ):
        road_gdf = pd.read_csv(csv_path, sep=sep)
        val_cols = [
            c for c in road_gdf.columns if c.startswith("F_")
        ]  # Find everything starting with 'F'
        return cls(road_gdf, val_cols, representative_damage_percentage)

    ### Controlers for return period based damage and risk calculations
    def main(self, damage_function: DamageCurveEnum, manual_damage_functions):
        """
        Control the damage calculation per return period

        """

        assert len(self.return_periods) > 0, "no return periods identified"
        assert "me" in self.stats, "mean water depth (key: me) is missing"
        assert "fr" in self.stats, "inundated fraction (key: fr) is missing"

        self.do_cleanup_and_mask_creation()

        if damage_function == DamageCurveEnum.HZ:
            self.calculate_damage_HZ(events=self.return_periods)

        if damage_function == DamageCurveEnum.OSD:
            self.calculate_damage_OSdaMage(events=self.return_periods)

        if damage_function == DamageCurveEnum.MAN:
            self.calculate_damage_manual_functions(
                events=self.return_periods,
                manual_damage_functions=manual_damage_functions,
            )

    def control_risk_calculation(
        self,
        damage_function: DamageCurveEnum,
        mode: RiskCalculationModeEnum,
        year: int,
    ):
        """
        Controller of the risk calculation, which calls the correct risk (integration) functions

        Arguments:
            *damage_function* (DamageCurveEnum) : defines the damage estimation method
            *mode* (RiskCalculationModeEnum) : the sort of risk calculation that you want to do, can be:
                                ‘default’, 'cut_from_YYYY_year’, ‘triangle_to_null_YYYY_year’
            *year* (int) : the cutoff year/return period of the risk calculation
            :param damage_function:
        """
        self.verify_damage_data_for_risk_calculation()

        # prepare the parameters of the risk calculation
        to_integrate_shaper = ToIntegrateShaperFactory.get_shaper(
            gdf=self.gdf, damage_function=damage_function
        )
        return_periods = to_integrate_shaper.get_return_periods()
        _to_integrate_dict = to_integrate_shaper.shape_to_integrate_object(
            return_periods=return_periods
        )

        for vulnerability_curve_name, _to_integrate in _to_integrate_dict.items():
            if mode == RiskCalculationModeEnum.DEFAULT:
                _to_integrate = self.rework_damage_data_default(_to_integrate)
                _risk = self.integrate_df_trapezoidal(_to_integrate.copy())

            _rps = list(_to_integrate.columns)

            if mode == RiskCalculationModeEnum.CUT_FROM_YEAR:
                """
                In this mode, the integration mimics the presence of a flood protection
                """

                if year <= min(_rps):
                    raise ValueError(
                        """
                    RA2CE cannot calculate risk in 'cut_from' mode if 
                    Return period of the cutoff ({}) <= smallest available return period ({})
                    Use 'default' mode or 'triangle_to_null_mode' instead.
                                        """.format(
                            year, min(_rps)
                        )
                    )

                elif (
                    min(_rps) < year < max(_rps)
                ):  # if protection level is between min and max RP
                    _to_integrate = self.rework_damage_data_cut_from(
                        _to_integrate, year
                    )
                    _risk = self.integrate_df_trapezoidal(_to_integrate.copy())

                elif year >= max(
                    _rps
                ):  # cutoff is larger or equal than largest return period
                    # risk is return frequency of cutoff
                    # times the damage of the most extreme event
                    _to_integrate = _to_integrate.fillna(0)
                    _risk = _to_integrate[max(_to_integrate.columns)] / year

            elif mode == RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR:
                """
                In this mode, an extra data point with zero damage is added at some distance from the smallest known RP,
                and the area of the Triangle this creates is also calculated
                """

                if year >= min(_rps) and year != 0:
                    raise ValueError(
                        """
                    RA2CE cannot calculate risk in 'triangle_to_null' mode if 
                    Return period of the triangle ({}) >= smallest available return period ({})
                    Use 'default' mode or 'cut_from' instead.
                                        """.format(
                            year, min(_rps)
                        )
                    )

                if year == 0:
                    logging.warning(
                        "Available lane data cannot simply be converted to float/int, RA2CE will try a clean-up."
                    )
                    year = 1

                _to_integrate = self.rework_damage_data_triangle_to_null(
                    _to_integrate, year
                )
                _risk = self.integrate_df_trapezoidal(_to_integrate.copy())

            self.gdf[f"risk_{vulnerability_curve_name}"] = _risk

    def verify_damage_data_for_risk_calculation(self):
        """
        Do some data quality and requirement checks before starting the risk calculation

        :return:
        """
        # Check if there is only one unique damage function
        # RP should in the column name
        pass

    @staticmethod
    def integrate_df_trapezoidal(df: pd.DataFrame) -> np.array:
        """
        Arguments:
            *df* (pd.DataFrame) :
                Column names should contain return periods (years)
                Each row should contain a set of damages for one object

        Returns:
            np.array : integrated result per row

        """
        # convert return periods to frequencies
        df.columns = [1 / RP for RP in df.columns]
        # sort columns by ascending frequency
        df = df.sort_index(axis="columns")
        values = df.values
        frequencies = df.columns
        return np.trapz(values, frequencies, axis=1)

    @staticmethod
    def rework_damage_data_default(to_integrate: pd.DataFrame) -> pd.DataFrame:
        """
        Rework the damage data to make it suitable for integration (risk calculation) in default mode

        :param _to_integrate:
        :return: _to_integrate
        """
        # Copy the maximum return period with an infinitely high damage
        _max_return_period = max(to_integrate.columns)
        to_integrate[float("inf")] = to_integrate[_max_return_period]

        # Stop integrating at the last known return period, so no further manipulation needed
        _min_return_period = min(to_integrate.columns)

        to_integrate = to_integrate.fillna(0)

        logging.info(
            """Risk calculation runs in 'default' mode. 
                    Assumptions:
                        - for all return periods > max RP{}, damage = dam_RP{}
                        - for all return periods < min RP{}, damage = 0

                    """.format(
                _max_return_period, _max_return_period, _min_return_period
            )
        )
        return to_integrate

    @staticmethod
    def rework_damage_data_cut_from(
        to_integrate: pd.DataFrame, cutoff_rp: int
    ) -> pd.DataFrame:
        """
        Rework the damage data to make it suitable for integration (risk calculation) in default mode

        :param _to_integrate:
                _cutoff_rp : the return period at which to make the cutoff, aka the flood protection level
        :return: _to_integrate
        """
        _rps = list(to_integrate.columns)

        if cutoff_rp in _rps:
            _dropcols = [rp for rp in _rps if rp < cutoff_rp]
            to_integrate = to_integrate.drop(columns=_dropcols)
        else:
            # find position of first RP value < PL
            # pos = _rps.index(next(i for i in _rps if i < _cutoff_rp))
            # _to_integrate = _to_integrate[_rps[0:pos+1]] #remove all the values with smaller RPs than the PL

            _frequencies = to_integrate.copy()
            _frequencies.columns = [1 / c for c in _frequencies.columns]

            _frequencies[1 / cutoff_rp] = np.nan
            _frequencies = _frequencies.interpolate(method="index", axis=1)

            # Drop the columns outside the cutoff
            _dropcols = [c for c in _frequencies.columns if c > 1 / cutoff_rp]
            _frequencies = _frequencies.drop(columns=_dropcols)

            to_integrate = _frequencies
            to_integrate.columns = [1 / c for c in to_integrate.columns]

            # Copy the maximum return period with an infinitely high damage
            _max_return_period = max(to_integrate.columns)
            to_integrate[float("inf")] = to_integrate[_max_return_period]

            to_integrate = to_integrate.fillna(0)

        logging.info(
            """Risk calculation runs in 'cut_from' mode. 
                                Assumptions:
                                    - for all return periods > max RP{}, damage = dam_RP{}
                                    - damage at cutoff is linearly interpolated from known damages
                                    - no damage for al RPs > RP_cutoff ({})

                                """.format(
                _max_return_period, _max_return_period, cutoff_rp
            )
        )

        return to_integrate

    @staticmethod
    def rework_damage_data_triangle_to_null(
        to_integrate: pd.DataFrame, triangle_end: float
    ) -> pd.DataFrame:
        """
        Rework the damage data to make it suitable for integration (risk calculation) in default mode

        :param _to_integrate:
                _triangle_end_rp : the return period at to end the triangle
        :return: _to_integrate
        """
        # Copy the maximum return period with an infinitely high damage
        _max_return_period = max(to_integrate.columns)
        to_integrate[float("inf")] = to_integrate[_max_return_period]

        # At the return period of the triangle end, set all damage values to zero
        to_integrate[triangle_end] = 0

        to_integrate = to_integrate.sort_index(
            axis="columns", ascending=False
        )  # from large to small RP

        to_integrate = to_integrate.fillna(0)

        logging.info(
            """Risk calculation runs in 'triangle to null' mode. 
                                Assumptions:
                                    - for all return periods > max RP{}, damage = dam_RP{}
                                    - at the end of the triangle {}, damage = 0

                                """.format(
                _max_return_period, _max_return_period, triangle_end
            )
        )
        return to_integrate
