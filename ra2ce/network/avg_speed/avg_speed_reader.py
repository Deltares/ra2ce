from pathlib import Path

import pandas as pd

from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol
from ra2ce.network.avg_speed.avg_speed import AvgSpeed


class AvgSpeedReader(FileReaderProtocol):
    def read(self, file_path: Path) -> AvgSpeed:
        _avg_speed_data = pd.read_csv(file_path)
        _avg_speed = AvgSpeed()
        for _, row in _avg_speed_data.iterrows():
            _avg_speed.set_avg_speed(row["road_types"], row["avg_speed"])
        return _avg_speed
