from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class AggregateWlEnum(Ra2ceEnumBase):
    NONE = 0
    MIN = 1
    MAX = 2
    MEAN = 3
    INVALID = 99

    def get_suffix(self):
        return self.name[:2].lower()
