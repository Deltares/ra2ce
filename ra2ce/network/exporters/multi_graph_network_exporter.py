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

from geopandas import GeoDataFrame

from ra2ce.network.exporters.geodataframe_network_exporter import (
    GeoDataFrameNetworkExporter,
)
from ra2ce.network.exporters.network_exporter_base import (
    MULTIGRAPH_TYPE,
    NetworkExporterBase,
)
from ra2ce.network.networks_utils import get_nodes_and_edges_from_origin_graph


class MultiGraphNetworkExporter(NetworkExporterBase):
    pickle_path: Optional[Path]

    def export_to_gpkg(self, output_dir: Path, export_data: MULTIGRAPH_TYPE) -> None:
        if not output_dir.is_dir():
            output_dir.mkdir(parents=True)

        _nodes_graph, _edges_graph = get_nodes_and_edges_from_origin_graph(export_data)

        def export_gdf(gdf_data: GeoDataFrame, suffix: str):
            """
            Different from `GeoDataFrameNetworkExporter` at `index=True`.
            """
            _export_file = output_dir.joinpath(self.basename + suffix + ".gpkg")
            gdf_data.to_file(_export_file, index=True, driver="GPKG", encoding="utf-8")
            logging.info("Saved %s in %s.", _export_file.stem, output_dir)

        export_gdf(_edges_graph, "_edges")
        export_gdf(_nodes_graph, "_nodes")

    def export_to_pickle(self, output_dir: Path, export_data: MULTIGRAPH_TYPE) -> None:
        self.pickle_path = output_dir.joinpath(self.basename + ".p")
        with open(self.pickle_path, "wb") as f:
            pickle.dump(export_data, f, protocol=4)
        logging.info(
            "Saved %s in %s.", self.pickle_path.stem, self.pickle_path.resolve().parent
        )
