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


import json
import logging
from pathlib import Path
from typing import Any

from ra2ce.common.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol


class JsonExporter(Ra2ceExporterProtocol):
    def export(self, export_path: Path, export_data: Any) -> None:
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
