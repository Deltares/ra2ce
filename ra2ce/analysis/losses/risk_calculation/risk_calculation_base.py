from abc import ABC, abstractmethod

import geopandas as gpd
import numpy as np
import re


class RiskCalculationBase(ABC):
    risk_calculation_year: int
    losses_gdf: gpd.GeoDataFrame

    def __init__(self, risk_calculation_year: int, losses_gdf: gpd.GeoDataFrame):
        self.risk_calculation_year = risk_calculation_year
        self.losses_gdf = losses_gdf
        self.__post_init__()

    def __post_init__(self):
        """Private method to __post_init__ computed attributes."""
        self._to_integrate = self._get_to_integrate()
        self._rework_damage_data()

    @property
    def return_periods(self) -> set[int]:
        return self._get_return_periods()

    @property
    def max_return_period(self) -> int:
        return max(self.return_periods)

    @property
    def min_return_period(self) -> int:
        return min(self.return_periods)

    def _get_return_periods(self):
        # Find the hazard columns; these may be events or return periods
        hazard_column = [c for c in self.losses_gdf.columns if c.startswith("RP")]
        return_periods = set(
            [float(x.split("_")[0].replace("RP", "")) for x in hazard_column]
        )  # set of unique return_periods
        return return_periods

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
    def _rework_damage_data(self):
        pass

    def integrate_df_trapezoidal(self) -> np.array:
        """
        Arguments:
            *df* (pd.DataFrame) :
                Column names should contain return periods (years)
                Each row should contain a set of damages for one object

        Returns:
            np. Array : integrated result per row

        """
        # convert return periods to frequencies
        _to_integrate = self._to_integrate.copy()
        _to_integrate.columns = sorted(1 / rp for rp in self._to_integrate.columns)
        values = _to_integrate.values
        frequencies = _to_integrate.columns
        return np.trapz(values, frequencies, axis=1)
