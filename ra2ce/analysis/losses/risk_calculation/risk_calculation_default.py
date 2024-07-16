from abc import ABC
import geopandas as gpd
import logging

from ra2ce.analysis.losses.risk_calculation.risk_calculation_base import (
    RiskCalculationBase,
)


class RiskCalculationDefault(RiskCalculationBase, ABC):
    def __init__(self, risk_calculation_year: int, losses_gdf: gpd.GeoDataFrame):
        super().__init__(risk_calculation_year, losses_gdf)

    def rework_damage_data(self) -> gpd.GeoDataFrame:
        """
        Rework the damage data to make it suitable for integration (risk calculation) in default mode
        """
        # Copy the maximum return period with an infinitely high damage
        self._to_integrate[float("inf")] = self._to_integrate[self.max_return_period]

        # Stop integrating at the last known return period, so no further manipulation needed
        self._to_integrate = self._to_integrate.fillna(0)

        logging.info(
            """Risk calculation runs in 'default' mode. 
                    Assumptions:
                        - for all return periods > max RP{}, damage = dam_RP{}
                        - for all return periods < min RP{}, damage = 0

                    """.format(
                self.max_return_period, self.max_return_period, self.min_return_period
            )
        )
        return self._to_integrate
