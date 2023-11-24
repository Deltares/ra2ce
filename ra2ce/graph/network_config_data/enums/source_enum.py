from __future__ import annotations

from enum import Enum


class SourceEnum(Enum):
    OSB_BPF = 1
    OSM_DOWNLOAD = 2
    SHAPEFILE = 3
    PICKLE = 4
    INVALID = 99

    @classmethod
    def get_enum(cls, input: str) -> SourceEnum:
        try:
            return cls[input.replace(" ", "_").upper()]
        except KeyError:
            return cls.INVALID

    @property
    def old_name(self) -> str:
        """
        Converts the enum name back to the input name
        """
        _parts = self.name.split("_")
        return " ".join(
            [_part if len(_part) == 3 else _part.lower() for _part in _parts]
        )
