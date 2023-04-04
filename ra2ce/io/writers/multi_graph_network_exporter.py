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
import pickle
from pathlib import Path
from typing import Optional

from ra2ce.graph.networks_utils import graph_to_gpkg
from ra2ce.io.writers.network_exporter_base import MULTIGRAPH_TYPE, NetworkExporterBase


class MultiGraphNetworkExporter(NetworkExporterBase):
    pickle_path: Optional[Path]

    def export_to_shp(self, output_dir: Path, export_data: MULTIGRAPH_TYPE) -> None:
        if not output_dir.is_dir():
            output_dir.mkdir(parents=True)

        # TODO: This method should be a writer itself.
        graph_to_gpkg(
            export_data,
            output_dir / (self._basename + "_edges.gpkg"),
            output_dir / (self._basename + "_nodes.gpkg"),
        )
        logging.info(
            f"Saved {self._basename + '_edges.shp'} and {self._basename + '_nodes.shp'} in {output_dir}."
        )

    def export_to_pickle(self, output_dir: Path, export_data: MULTIGRAPH_TYPE) -> None:
        self.pickle_path = output_dir / (self._basename + ".p")
        with open(self.pickle_path, "wb") as f:
            pickle.dump(export_data, f, protocol=4)
        logging.info(
            f"Saved {self.pickle_path.stem} in {self.pickle_path.resolve().parent}."
        )
