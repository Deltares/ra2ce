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
from copy import deepcopy
from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_result.analysis_result_wrapper_protocol import (
    AnalysisResultWrapperProtocol,
)


class AnalysisResultWrapperExporter:
    def export_result(
        self,
        result_wrapper: AnalysisResultWrapperProtocol,
    ):
        """
        Exports the given result into the analysis requested formats ( `.gpkg` and / or `.csv`).

        Args:
            result_wrapper (AnalysisResultWrapper): The result to export.
        """
        if not result_wrapper.is_valid_result():
            return

        for _analysis_result in result_wrapper.results_collection:
            if _analysis_result.analysis_config.save_gpkg:
                self._export_gdf(
                    _analysis_result.analysis_result,
                    _analysis_result.base_export_path.with_suffix(".gpkg"),
                )
            if _analysis_result.analysis_config.save_csv:
                self._export_csv(
                    _analysis_result.analysis_result,
                    _analysis_result.base_export_path.with_suffix(".csv"),
                )

    def _export_gdf(self, gdf: GeoDataFrame, export_path: Path):
        """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

        Arguments:
            gdf [geodataframe]: geodataframe object to be converted
            export_path [Path]: path to save
        """
        # save to shapefile
        gdf.crs = "epsg:4326"  # TODO: decide if this should be variable with e.g. an output_crs configured

        for col in gdf.columns:
            if gdf[col].dtype == object and col != gdf.geometry.name:
                gdf[col] = gdf[col].astype(str)

        if export_path.exists():
            export_path.unlink()
        if not export_path.parent.exists():
            export_path.parent.mkdir(parents=True)

        gdf.to_file(export_path, driver="GPKG")
        logging.info("Results saved to: %s", export_path)

    def _export_csv(self, result_gdf: GeoDataFrame, export_path: Path):
        if not export_path.parent.exists():
            export_path.parent.mkdir(parents=True)

        _result_copy = deepcopy(result_gdf)
        del _result_copy["geometry"]
        _result_copy.to_csv(export_path, index=False)
