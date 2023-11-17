from pathlib import Path
from typing import Optional

from attr import dataclass


@dataclass
class HazardFiles:
    tif: Optional[list[Path]] = None
    shp: Optional[list[Path]] = None
    table: Optional[list[Path]] = None
