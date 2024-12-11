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

import geopandas as gpd

from ra2ce.network.exporters.network_exporter_base import NetworkExporterBase


class GeoDataFrameNetworkExporter(NetworkExporterBase):
    def export_to_gpkg(self, output_dir: Path, export_data: gpd.GeoDataFrame) -> None:
        _output_gpkg_path = output_dir.joinpath(self.basename + ".gpkg")

        if _output_gpkg_path.exists():
            logging.info("Removing previous gpkg file %s.", _output_gpkg_path)
            _output_gpkg_path.unlink()

        export_data.to_file(
            _output_gpkg_path, index=False, driver="GPKG", encoding="utf-8"
        )
        logging.info("Saved %s in %s.", _output_gpkg_path.stem, output_dir)

    def export_to_pickle(self, output_dir: Path, export_data: gpd.GeoDataFrame) -> None:
        self.pickle_path = output_dir.joinpath(self.basename + ".feather")
        export_data.to_feather(self.pickle_path, index=False)
        logging.info("Saved %s in %s.", self.pickle_path.stem, output_dir)
