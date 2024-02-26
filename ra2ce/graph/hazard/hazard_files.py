from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HazardFiles:
    tif: list[Path] = field(default_factory=list)
    gpkg: list[Path] = field(default_factory=list)
    table: list[Path] = field(default_factory=list)
