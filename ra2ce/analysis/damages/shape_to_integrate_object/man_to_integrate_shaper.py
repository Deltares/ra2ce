import re

import geopandas as gpd
import pandas as pd

from ra2ce.analysis.damages.shape_to_integrate_object.to_Integrate_shaper_protocol import (
    ToIntegrateShaperProtocol,
)


class ManToIntegrateShaper(ToIntegrateShaperProtocol):
    gdf: gpd.GeoDataFrame

    def __init__(self, gdf):
        self.gdf = gdf

    @staticmethod
    def _extract_columns_by_pattern(
        pattern_text: str, gdf: gpd.GeoDataFrame
    ) -> set[str]:
        """
        Extract column names based on the provided regex pattern.

        Args:
            pattern_text (Pattern[str]): The compiled regex pattern to match the column names.
            df (pd.DataFrame): The DataFrame from which to extract the RP values.

        Returns:
            Set[str]: A set of RP values extracted from the column names.
        """
        pattern = re.compile(pattern_text)
        columns = {pattern.search(c).group(1) for c in gdf.columns if pattern.search(c)}
        return columns

    def get_return_periods(self) -> list:
        # Extract the RP values from the columns
        rp_values = ManToIntegrateShaper._extract_columns_by_pattern(
            pattern_text=r"RP(\d+)", gdf=self.gdf
        )
        if not rp_values:
            raise ValueError("No damage column with RP found")

        return sorted([float(rp) for rp in rp_values])

    def shape_to_integrate_object(
        self, return_periods: list
    ) -> dict[str : gpd.GeoDataFrame]:
        _to_integrate_dict = {}
        # finds vulnerability curves shown with Ci, where 1<= i <=6
        vulnerability_curves = sorted(
            ManToIntegrateShaper._extract_columns_by_pattern(
                pattern_text=r"dam_RP\d+_(.*)", gdf=self.gdf
            )
        )
        for vulnerability_curve in vulnerability_curves:

            filtered_columns = sorted(
                ManToIntegrateShaper._extract_columns_by_pattern(
                    pattern_text=rf"(dam_RP\d+.*{vulnerability_curve})",
                    gdf=self.gdf,
                )
            )
            _to_integrate = self.gdf[filtered_columns]

            _to_integrate.columns = [
                float(c.split("_")[1].replace("RP", "")) for c in _to_integrate.columns
            ]
            _to_integrate_dict[f"{vulnerability_curve}"] = _to_integrate.sort_index(
                axis="columns", ascending=False
            )

        return _to_integrate_dict
