import re
from abc import ABC, abstractmethod

import geopandas as gpd
import numpy as np


class RiskCalculationBase(ABC):
    risk_calculation_year: int
    losses_gdf: gpd.GeoDataFrame
    _return_periods: set[int]

    def __init__(self, risk_calculation_year: int, losses_gdf: gpd.GeoDataFrame):
        self.risk_calculation_year = risk_calculation_year
        self.losses_gdf = losses_gdf
        self._return_periods = self._get_return_periods()

    @property
    def return_periods(self):
        return self._return_periods

    @property
    def _max_return_period(self) -> int:
        return max(self.return_periods)

    @property
    def _min_return_period(self) -> int:
        return min(self.return_periods)

    def _get_return_periods(self) -> set:
        # Find the hazard columns; these may be events or return periods
        hazard_column = [c for c in self.losses_gdf.columns if c.startswith("RP")]
        rps = set(
            [float(x.split("_")[0].replace("RP", "")) for x in hazard_column]
        )  # set of unique rps
        return rps

    def _get_to_integrate(self) -> gpd.GeoDataFrame:
        def _extract_columns_by_pattern(
            pattern_text: str, gdf: gpd.GeoDataFrame
        ) -> set[str]:
            """
            Extract column names based on the provided regex pattern.
            """
            pattern = re.compile(pattern_text)
            columns = {
                pattern.search(c).group(1) for c in gdf.columns if pattern.search(c)
            }
            return columns

        loss_columns = sorted(
            _extract_columns_by_pattern(
                pattern_text=r"(vlh.*.total)", gdf=self.losses_gdf
            )
        )
        loss_columns = [c for c in loss_columns if c.split("_")[1].startswith("RP")]

        _to_integrate = self.losses_gdf[loss_columns].copy()

        _to_integrate.columns = [
            float(c.split("_")[1].replace("RP", "")) for c in _to_integrate.columns
        ]
        return _to_integrate

    @abstractmethod
    def _get_network_risk_calculations(self) -> gpd.GeoDataFrame:
        pass

    def get_integration_of_df_trapezoidal(self) -> np.array:
        """
        Arguments:
            *df* (pd.DataFrame) :
                Column names should contain return periods (years)
                Each row should contain a set of damages for one object

        Returns:
            np. Array : integrated result per row

        """
        _risk_calculations = self._get_network_risk_calculations()
        frequencies = sorted(1 / rp for rp in _risk_calculations.columns)
        return np.trapz(_risk_calculations.values, frequencies, axis=1)
