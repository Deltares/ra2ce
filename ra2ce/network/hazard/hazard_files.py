from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HazardFiles:
    tif: list[Path] = field(default_factory=list)
    gpkg: list[Path] = field(default_factory=list)
    table: list[Path] = field(default_factory=list)

    @classmethod
    def from_hazard_map(cls, hazard_map: list[Path]) -> HazardFiles:
        """
        Create a HazardFiles object from a list of hazard map files.

        Args:
            hazard_map (list[Path]): _description_

        Returns:
            HazardFiles: _description_
        """

        def _get_filtered_files(*suffix) -> list[Path]:
            _filter = lambda x: x.suffix in list(suffix)
            return list(filter(_filter, hazard_map))

        return cls(
            tif=_get_filtered_files(".tif"),
            gpkg=_get_filtered_files(".gpkg"),
            table=_get_filtered_files(".csv"),
        )
