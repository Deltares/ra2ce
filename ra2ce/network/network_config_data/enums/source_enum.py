from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class SourceEnum(Ra2ceEnumBase):
    """
    Enumeration of data source types.

    This enum defines identifiers for different input data formats or
    sources used for the network definition.

    Attributes
    ----------
    OSB_BPF : int
        Binary Packed File (BPF) format from OSB pipeline (1).
    OSM_DOWNLOAD : int
        Data downloaded directly from OpenStreetMap (OSM) (2).
    SHAPEFILE : int
        ESRI Shapefile format (3).
    PICKLE : int
        Python Pickle serialized object (4).
    INVALID : int
        Invalid or unsupported data source (99).

    """
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
