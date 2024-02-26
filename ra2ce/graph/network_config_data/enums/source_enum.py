from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class SourceEnum(Ra2ceEnumBase):
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
    def config_value(self) -> str:
        _parts = self.name.split("_")
        return " ".join(
            [_part if len(_part) == 3 else _part.lower() for _part in _parts]
        )
