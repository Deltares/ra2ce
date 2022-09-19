import json
import logging
from pathlib import Path
from typing import Any

from ra2ce.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol


class JsonExporter(Ra2ceExporterProtocol):
    def export(export_path: Path, export_data: Any) -> None:
        """
        Exports into JSON the given data at the given path. When the parent(s) directory does not exist then it will be created.

        Args:
            export_path (Path): File path where to store the final 'json' file.
            export_data (Any): Data to export.
        """
        _export_dir = export_path.parent
        if not _export_dir.is_dir():
            _export_dir.mkdir(parents=True)

        with open(export_path, "w") as _export_strem:
            json.dump(export_data, _export_strem)
            logging.info(f"Saved (or overwrote) {export_path.name}")
