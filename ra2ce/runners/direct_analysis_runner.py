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
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.direct.analysis_direct_protocol import AnalysisDirectProtocol
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.runners.analysis_runner_protocol import AnalysisRunner


class DirectAnalysisRunner(AnalysisRunner):
    def __str__(self) -> str:
        return "Direct Analysis Runner"

    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        if (
            not ra2ce_input.analysis_config
            or not ra2ce_input.analysis_config.config_data.direct
        ):
            return False
        if not ra2ce_input.network_config:
            return False
        _network_config = ra2ce_input.network_config.config_data
        if not _network_config.hazard or not _network_config.hazard.hazard_map:
            logging.error(
                "Please define a hazardmap in your network.ini file. Unable to calculate direct damages."
            )
            return False
        return True

    def save_gdf(self, gdf: GeoDataFrame, save_path: Path, driver: str):
        """Takes in a geodataframe object and outputs shapefiles at the paths indicated by edge_shp and node_shp

        Arguments:
            gdf [geodataframe]: geodataframe object to be converted
            save_path [Path]: path to save
            driver [str]: defines the file format
        Returns:
            None
        """
        # save to shapefile
        gdf.crs = "epsg:4326"  # TODO: decide if this should be variable with e.g. an output_crs configured

        for col in gdf.columns:
            if gdf[col].dtype == object and col != gdf.geometry.name:
                gdf[col] = gdf[col].astype(str)

        if save_path.exists():
            save_path.unlink()
        gdf.to_file(save_path, driver=driver)
        logging.info("Results saved to: {}".format(save_path))

    def save_result(
        self, analysis: AnalysisDirectProtocol, analysis_config: AnalysisConfigWrapper
    ):
        if analysis.result is None or analysis.result.empty:
            return

        _output_path = analysis_config.config_data.output_path.joinpath(
            analysis.analysis.analysis.config_value
        )

        if analysis.analysis.save_gpkg:
            gpkg_path = _output_path.joinpath(
                analysis.analysis.name.replace(" ", "_") + ".gpkg"
            )
            self.save_gdf(analysis.result, gpkg_path, "GPKG")
        if analysis.analysis.save_csv:
            csv_path = _output_path.joinpath(
                analysis.analysis.name.replace(" ", "_") + ".csv"
            )
            del analysis.result["geometry"]
            analysis.result.to_csv(csv_path, index=False)

    def run(self, analysis_config: AnalysisConfigWrapper) -> None:
        _analysis_collection = AnalysisCollection.from_config(analysis_config)
        for analysis in _analysis_collection.direct_analyses:
            logging.info(
                f"----------------------------- Started analyzing '{analysis.analysis.name}'  -----------------------------"
            )
            starttime = time.time()

            analysis.result = analysis.execute()

            self.save_result(analysis, analysis_config)

            endtime = time.time()
            logging.info(
                f"----------------------------- Analysis '{analysis.analysis.name}' finished. "
                f"Time: {str(round(endtime - starttime, 2))}s  -----------------------------"
            )
