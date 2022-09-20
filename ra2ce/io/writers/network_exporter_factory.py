from pathlib import Path
from typing import List, Type

import geopandas as gpd
import networkx as nx

from ra2ce.io.writers.geodataframe_network_exporter import GeoDataFrameNetworkExporter
from ra2ce.io.writers.multi_graph_network_exporter import MultiGraphNetworkExporter
from ra2ce.io.writers.network_exporter_base import (
    NETWORK_TYPE,
    NetworkExporterBase,
)


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
