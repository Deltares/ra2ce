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
import time
from pathlib import Path

from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_wrapper import (
    AnalysisConfigWrapper,
)
from ra2ce.analysis.analysis_result_wrapper import IndirectAnalysisResultWrapper
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class IndirectAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Indirect Analysis Runner"

    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        if (
            not ra2ce_input.analysis_config
            or not ra2ce_input.analysis_config.config_data.indirect
        ):
            return False
        return True

    def _save_gdf(self, gdf: GeoDataFrame, save_path: Path, driver: str):
        """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

        Arguments:
            gdf [geodataframe]: geodataframe object to be converted
            save_path [Path]: path to save
            driver [str]: defines the file format

        Returns:
            None
        """
        # save to shapefile
        # TODO: decide if this should be variable with e.g. an output_crs configured
        gdf.crs = "epsg:4326"

        for col in gdf.columns:
            if gdf[col].dtype == object and col != gdf.geometry.name:
                gdf[col] = gdf[col].astype(str)

        if save_path.exists():
            save_path.unlink()
        gdf.to_file(save_path, driver=driver)
        logging.info("Results saved to: %s", save_path)

    def _save_result(self, result_wrapper: IndirectAnalysisResultWrapper):
        if not result_wrapper.is_valid_result():
            return

        _analysis = result_wrapper.analysis
        _analysis_name = _analysis.analysis.name.replace(" ", "_")

        _output_path = _analysis.output_path.joinpath(
            _analysis.analysis.analysis.config_value
        )

        if _analysis.analysis.save_gpkg:
            gpkg_path = _output_path.joinpath(_analysis_name + ".gpkg")
            self._save_gdf(result_wrapper.analysis_result, gpkg_path, "GPKG")
        if _analysis.analysis.save_csv:
            csv_path = _output_path.joinpath(_analysis_name + ".csv")
            del result_wrapper.analysis_result["geometry"]
            result_wrapper.analysis_result.to_csv(csv_path, index=False)

    def run(
        self, analysis_config: AnalysisConfigWrapper
    ) -> list[IndirectAnalysisResultWrapper]:
        _analysis_collection = AnalysisCollection.from_config(analysis_config)
        _results = []
        for analysis in _analysis_collection.indirect_analyses:
            logging.info(
                "----------------------------- Started analyzing '%s'  -----------------------------",
                analysis.analysis.name,
            )
            starttime = time.time()

            _result = analysis.execute()
            _result_wrapper = IndirectAnalysisResultWrapper(
                analysis_result=_result, analysis=analysis
            )

            _results.append(_result_wrapper)
            self._save_result(_result_wrapper)

            endtime = time.time()
            logging.info(
                "----------------------------- Analysis '%s' finished. "
                "Time: %ss  -----------------------------",
                analysis.analysis.name,
                str(round(endtime - starttime, 2)),
            )
        return _results
