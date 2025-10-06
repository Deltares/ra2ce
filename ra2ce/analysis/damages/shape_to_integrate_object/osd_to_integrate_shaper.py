import re

import geopandas as gpd
import pandas as pd

from ra2ce.analysis.damages.shape_to_integrate_object.to_Integrate_shaper_protocol import (
    ToIntegrateShaperProtocol,
)


class OsdToIntegrateShaper(ToIntegrateShaperProtocol):
    """
    Shapes OSD (Origin-Destination) hazard data for integration.

    Attributes:
        gdf (GeoDataFrame): Input GeoDataFrame containing hazard data.
    """

    gdf: gpd.GeoDataFrame

    def __init__(self, gdf):
        """
        Initialize the shaper with a GeoDataFrame.

        Args:
            gdf: GeoDataFrame containing hazard data.
        """
        self.gdf = gdf

    @staticmethod
    def _extract_columns_by_pattern(
        pattern_text: str, gdf: gpd.GeoDataFrame
    ) -> set[str]:
        """
        Extract column names based on the provided regex pattern.

        Args:
            pattern_text (Pattern[str]): The compiled regex pattern to match the column names.
            gdf (pd.DataFrame): The DataFrame from which to extract the RP values.

        Returns:
            set[str]: A set of RP values extracted from the column names.
        """
        pattern = re.compile(pattern_text)
        columns = {pattern.search(c).group(1) for c in gdf.columns if pattern.search(c)}
        return columns

    def get_return_periods(self) -> list:
        """
        Extract all return periods (RP) from the GeoDataFrame columns.

        Returns:
            list[float]: Sorted list of return periods.

        Raises:
            ValueError: If no columns matching the RP pattern are found.
        """
        # Extract the RP values from the columns
        rp_values = OsdToIntegrateShaper._extract_columns_by_pattern(
            pattern_text=r"RP(\d+)", gdf=self.gdf
        )
        if not rp_values:
            raise ValueError("No damage column with RP found")

        return sorted([float(rp) for rp in rp_values])

    def shape_to_integrate_object(
        self, return_periods: list
    ) -> dict[str : gpd.GeoDataFrame]:
        """
        Shape the hazard data for integration based on selected return periods.

        Args:
            return_periods: List of return period column names to extract.

        Returns:
            dict[str, GeoDataFrame]: Dictionary mapping vulnerability curve names to
            GeoDataFrames containing the selected and sorted hazard data.
        """
        _to_integrate_dict = {}
        # finds vulnerability curves shown with Ci, where 1<= i <=6
        vulnerability_curves = sorted(
            OsdToIntegrateShaper._extract_columns_by_pattern(
                pattern_text=r"(C\d+)", gdf=self.gdf
            )
        )
        for vulnerability_curve in vulnerability_curves:

            filtered_columns = sorted(
                OsdToIntegrateShaper._extract_columns_by_pattern(
                    pattern_text=rf"(.*{vulnerability_curve}.*representative.*)",
                    gdf=self.gdf,
                )
            )
            _to_integrate = self.gdf[filtered_columns]

            _to_integrate.columns = [
                float(c.split("_")[2].replace("RP", "")) for c in _to_integrate.columns
            ]
            _to_integrate_dict[f"{vulnerability_curve}"] = _to_integrate.sort_index(
                axis="columns", ascending=False
            )

        return _to_integrate_dict
