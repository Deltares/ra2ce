from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class RoadTypeEnum(Ra2ceEnumBase):
    NONE = 0
    MOTORWAY = 1
    MOTORWAY_LINK = 2
    TRUNK = 3
    TRUNK_LINK = 4
    PRIMARY = 5
    PRIMARY_LINK = 6
    SECONDARY = 7
    SECONDARY_LINK = 8
    TERTIARY = 9
    TERTIARY_LINK = 10
    UNCLASSIFIED = 11
    RESIDENTIAL = 12
    ROAD = 13
    INVALID = 99
