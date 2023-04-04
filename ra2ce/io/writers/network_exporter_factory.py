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
from typing import List, Type

import geopandas as gpd
import networkx as nx

from ra2ce.io.writers.geodataframe_network_exporter import GeoDataFrameNetworkExporter
from ra2ce.io.writers.multi_graph_network_exporter import MultiGraphNetworkExporter
from ra2ce.io.writers.network_exporter_base import NETWORK_TYPE, NetworkExporterBase


class NetworkExporterFactory:
    def export(
        self,
        network: NETWORK_TYPE,
        basename: str,
        output_dir: Path,
        export_types: List[str],
    ) -> None:
        _exporter_type = self.get_exporter(network)
        self._exporter = _exporter_type(basename, export_types)
        self._exporter.export(output_dir, network)

    def get_pickle_path(self) -> Path:
        return self._exporter.pickle_path

    @staticmethod
    def get_exporter(network: NETWORK_TYPE) -> Type[NetworkExporterBase]:
        _network_type = type(network)
        if _network_type == gpd.GeoDataFrame:
            return GeoDataFrameNetworkExporter
        elif _network_type in [
            nx.classes.multigraph.MultiGraph,
            nx.classes.multidigraph.MultiDiGraph,
        ]:
            return MultiGraphNetworkExporter
