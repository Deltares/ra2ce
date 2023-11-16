from pathlib import Path
from typing import Optional

from attr import dataclass


@dataclass
class HazardFiles:
    tif: list[Optional[Path]] = None
    shp: list[Optional[Path]] = None
    table: list[Optional[Path]] = None
