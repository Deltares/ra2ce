from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class AggregateWlEnum(Ra2ceEnumBase):
    NONE = 0
    MIN = 1
    MAX = 2
    MEAN = 3
    INVALID = 99

    def get_wl_abbreviation(self):
        """gets the first two letters of the Enum.name used in hazard overlay, damages and losses analysis."""
        return self.name[:2].lower()
