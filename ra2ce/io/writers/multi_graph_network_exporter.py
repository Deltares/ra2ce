import logging
import pickle
from pathlib import Path
from typing import Optional

from ra2ce.graph.networks_utils import graph_to_shp
from ra2ce.io.writers.network_exporter_base import MULTIGRAPH_TYPE, NetworkExporterBase


class MultiGraphNetworkExporter(NetworkExporterBase):
    pickle_path: Optional[Path]

    def export_to_shp(self, output_dir: Path, export_data: MULTIGRAPH_TYPE) -> None:
        if not output_dir.is_dir():
            output_dir.mkdir(parents=True)

        # TODO: This method should be a writer itself.
        graph_to_shp(
            export_data,
            output_dir / (self._basename + "_edges.shp"),
            output_dir / (self._basename + "_nodes.shp"),
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
