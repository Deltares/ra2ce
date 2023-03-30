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


from pathlib import Path
from typing import Any, List, Union

import geopandas as gpd
import networkx as nx

from ra2ce.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol

MULTIGRAPH_TYPE = Union[
    nx.classes.multigraph.MultiGraph, nx.classes.multidigraph.MultiDiGraph
]
NETWORK_TYPE = Union[gpd.GeoDataFrame, MULTIGRAPH_TYPE]


class NetworkExporterBase(Ra2ceExporterProtocol):
    _export_types: List[str] = ["pickle"]

    def __init__(self, basename: str, export_types: List[str]) -> None:
        self._basename = basename
        self._export_types = export_types
        self.pickle_path = None

    def export_to_shp(self, output_dir: Path, export_data: NETWORK_TYPE) -> None:
        """
        Exports the given data into a `*.shp` file.

        Args:
            output_dir (Path): Output directory where the save the exported data.
            export_data (NETWORK_TYPE): Data that needs to be exported.
        """
        pass

    def export_to_pickle(self, output_dir: Path, export_data: NETWORK_TYPE) -> None:
        """
        Exports the given data into a `*.p` or `.feather` file.

        Args:
            output_dir (Path): Output directory where the save the exported data.
            export_data (NETWORK_TYPE): Data that needs to be exported.
        """
        pass

    def export(self, export_path: Path, export_data: Any) -> None:
        """
        Exports the given data to the specified types.
        TODO: I do not particularly like this approach, but at least gives better clarity on what the export options at the moment are.

        Args:
            export_path (Path): Path to the output directory where to export the data.
            export_data (Any): Data that needs to be exported.
        """
        if "pickle" in self._export_types:
            self.export_to_pickle(export_path, export_data)

        if "shp" in self._export_types:
            self.export_to_shp(export_path, export_data)
