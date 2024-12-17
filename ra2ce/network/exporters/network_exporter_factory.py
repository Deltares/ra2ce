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

import geopandas as gpd
import networkx as nx

from ra2ce.network.exporters.geodataframe_network_exporter import (
    GeoDataFrameNetworkExporter,
)
from ra2ce.network.exporters.multi_graph_network_exporter import (
    MultiGraphNetworkExporter,
)
from ra2ce.network.exporters.network_exporter_base import (
    NETWORK_TYPE,
    NetworkExporterBase,
)


class NetworkExporterFactory:
    _exporter: NetworkExporterBase

    def export(
        self,
        network: NETWORK_TYPE,
        basename: str,
        output_dir: Path,
        export_types: list[str],
    ) -> None:
        _exporter_type = self.get_exporter_type(network)
        self._exporter = _exporter_type(basename=basename, export_types=export_types)
        self._exporter.export(output_dir, network)

    def get_pickle_path(self) -> Path:
        return self._exporter.pickle_path

    @staticmethod
    def get_exporter_type(network: NETWORK_TYPE) -> type[NetworkExporterBase]:
        _network_type = type(network)
        if _network_type == gpd.GeoDataFrame:
            return GeoDataFrameNetworkExporter
        if _network_type in [
            nx.MultiGraph,
            nx.MultiDiGraph,
        ]:
            return MultiGraphNetworkExporter
        raise ValueError(f"Unsupported network type: {_network_type}")
