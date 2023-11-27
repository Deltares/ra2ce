from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class WeighingEnum(Ra2ceEnumBase):
    NONE = 0
    DISTANCE = 1
    LENGTH = 2
    TIME = 3
    INVALID = 99

    @classmethod
    def get_enum(cls, input: str | None) -> Ra2ceEnumBase:
        """
        Correct "distance" to "length"
        """
        if input and input == "distance":
            input = "length"
        _enum = super().get_enum(input)
        return _enum
