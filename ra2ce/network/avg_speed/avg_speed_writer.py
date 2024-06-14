from pathlib import Path

import pandas as pd

from ra2ce.common.io.writers.ra2ce_exporter_protocol import Ra2ceExporterProtocol
from ra2ce.network.avg_speed.avg_speed import AvgSpeed


class AvgSpeedWriter(Ra2ceExporterProtocol):
    def export(self, export_path: Path, export_data: AvgSpeed) -> None:
        export_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {
                "road_types": [x.config_value for x in export_data.speed_dict.keys()],
                "avg_speed": export_data.speed_dict.values(),
            }
        ).to_csv(export_path)
