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

from ra2ce.io.writers.network_exporter_base import NetworkExporterBase


class GeoDataFrameNetworkExporter(NetworkExporterBase):
    def export_to_shp(self, output_dir: Path, export_data: gpd.GeoDataFrame) -> None:
        _output_shp_path = output_dir / (self._basename + ".shp")
        export_data.to_file(
            _output_shp_path, index=False
        )  # , encoding='utf-8' -Removed the encoding type because this causes some shapefiles not to save.
        logging.info(f"Saved {_output_shp_path.stem} in {output_dir}.")

    def export_to_pickle(self, output_dir: Path, export_data: gpd.GeoDataFrame) -> None:
        self.pickle_path = output_dir / (self._basename + ".feather")
        export_data.to_feather(self.pickle_path, index=False)
        logging.info(f"Saved {self.pickle_path.stem} in {output_dir}.")
