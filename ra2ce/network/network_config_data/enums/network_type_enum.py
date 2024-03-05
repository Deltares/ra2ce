from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class NetworkTypeEnum(Ra2ceEnumBase):
    NONE = 0
    WALK = 1
    BIKE = 2
    DRIVE = 3
    DRIVE_SERVICE = 4
    ALL = 5
    INVALID = 99
