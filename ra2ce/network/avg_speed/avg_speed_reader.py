from pathlib import Path

import pandas as pd

from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol
from ra2ce.network.avg_speed.avg_speed import AvgSpeed
from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum


class AvgSpeedReader(FileReaderProtocol):
    def read(self, file_path: Path) -> AvgSpeed:
        _avg_speed = pd.read_csv(file_path)
        return AvgSpeed(
            speed_dict=dict(
                zip(
                    map(RoadTypeEnum.get_enum, _avg_speed["road_types"]),
                    _avg_speed["avg_speed"],
                )
            )
        )
