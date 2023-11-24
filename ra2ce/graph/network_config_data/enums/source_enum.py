from enum import Enum


class SourceEnum(Enum):
    OSB_BPF = 1
    OSM_DOWNLOAD = 2
    SHAPEFILE = 3
    PICKLE = 4
    INVALID = 99
