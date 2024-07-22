from abc import ABC
import geopandas as gpd
import logging

import numpy as np

from ra2ce.analysis.losses.risk_calculation.risk_calculation_base import (
    RiskCalculationBase,
)


class RiskCalculationCutFromYear(RiskCalculationBase):
    """
    In this mode, the integration mimics the presence of a flood protection
    """

    def _rework_damage_data(self):
        """
        Rework the damage data to make it suitable for integration (risk calculation) in cut_from_year mode
        """
        if self.risk_calculation_year <= self.min_return_period:
            raise ValueError(
                """
            RA2CE cannot calculate risk in 'cut_from' mode if 
            Return period of the cutoff ({}) <= smallest available return period ({})
            Use 'default' mode or 'triangle_to_null_mode' instead.
                                """.format(
                    self.risk_calculation_year, self.min_return_period
                )
            )
        elif (
            self.min_return_period < self.risk_calculation_year < self.max_return_period
        ):
            if self.risk_calculation_year in self.return_periods:
                _dropcols = [
                    rp for rp in self.return_periods if rp < self.risk_calculation_year
                ]
                self._to_integrate.drop(columns=_dropcols, inplace=True)
            else:
                # Copy the maximum return period with an infinitely high damage
                self._to_integrate[float("inf")] = self._to_integrate[
                    self.max_return_period
                ]

                self._to_integrate[self.risk_calculation_year] = np.nan
                self._to_integrate.interpolate(method="index", axis=1, inplace=True)

                _dropcols = [
                    c
                    for c in self._to_integrate.columns
                    if c < self.risk_calculation_year
                ]
                self._to_integrate.drop(columns=_dropcols, inplace=True)
                self._to_integrate = self._to_integrate.fillna(0)

                self._to_integrate = self._to_integrate[
                    sorted(self._to_integrate.columns, reverse=True)
                ]

            logging.info(
                """Risk calculation runs in 'cut_from' mode. 
                                    Assumptions:
                                        - for all return periods > max RP{}, damage = dam_RP{}
                                        - damage at cutoff is linearly interpolated from known damages
                                        - no damage for al RPs > RP_cutoff ({})
    
                                    """.format(
                    self.max_return_period,
                    self.max_return_period,
                    self.risk_calculation_year,
                )
            )

        elif (
            self.risk_calculation_year >= self.max_return_period
        ):  # cutoff is larger or equal than the largest return period
            # risk is return frequency of cutoff
            # times the damage to the most extreme event
            self._to_integrate = self._to_integrate.fillna(0)
            self._to_integrate[self.risk_calculation_year] = self._to_integrate[
                self.max_return_period
            ]
            self._to_integrate[float("inf")] = self._to_integrate[
                self.max_return_period
            ]
            self._to_integrate = self._to_integrate[
                [self.risk_calculation_year, float("inf")]
            ]
