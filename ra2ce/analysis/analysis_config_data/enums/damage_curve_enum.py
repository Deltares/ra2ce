from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class DamageCurveEnum(Ra2ceEnumBase):
    HZ = 1
    OSD = 2
    MAN = 3
    INVALID = 99

    @property
    def config_value(self) -> str | None:
        """
        Reconstruct the name as it is known in the config.
        This could entail replacement of " " by "_" and lower() operations.

        Returns:
            str: Value as known in the config.
        """
        if self.name == "NONE":
            return None
        return self.name
