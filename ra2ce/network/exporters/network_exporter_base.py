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


from dataclasses import dataclass, field
from pathlib import Path

import geopandas as gpd
import networkx as nx

from ra2ce.common.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol

MULTIGRAPH_TYPE = nx.MultiGraph | nx.MultiDiGraph
NETWORK_TYPE = gpd.GeoDataFrame | MULTIGRAPH_TYPE


@dataclass(kw_only=True)
class NetworkExporterBase(Ra2ceExporterProtocol):
    basename: str
    export_types: list[str] = field(default_factory=lambda: ["pickle"])
    pickle_path: Path = None

    def export_to_gpkg(self, output_dir: Path, export_data: NETWORK_TYPE) -> None:
        """
        Exports the given data into a `*.gpkg` file.

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

    def export(self, export_path: Path, export_data: NETWORK_TYPE) -> None:
        """
        Exports the given data to the specified types.
        TODO: I do not particularly like this approach, but at least gives better clarity on what the export options at the moment are.

        Args:
            export_path (Path): Path to the output directory where to export the data.
            export_data (NETWORK_TYPE): Data that needs to be exported.
        """
        if "pickle" in self.export_types:
            self.export_to_pickle(export_path, export_data)

        if "gpkg" in self.export_types:
            self.export_to_gpkg(export_path, export_data)
