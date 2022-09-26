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
