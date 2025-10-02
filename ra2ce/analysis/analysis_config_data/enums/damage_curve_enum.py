from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class DamageCurveEnum(Ra2ceEnumBase):
    """
    Enumeration of damage curve types for vulnerability assessment.

    This enum defines the types of damage curves that can be applied
    when estimating damages to roads or infrastructure. Each type
    represents a different model or methodology for translating an event
    magnitude into expected damage.

    Attributes
    ----------
    HZ : int
        Huizinga  damage curve (1).
    OSD : int
        OpenStreetMap-derived damage curve (2).
    MAN : int
        Manually defined damage curve (3).
    INVALID : int
        Invalid or unsupported damage curve type (99).
    """

    HZ = 1
    OSD = 2
    MAN = 3
    INVALID = 99

    @classmethod
    def get_enum(cls, input_str: str | None) -> DamageCurveEnum:
        return DamageCurveEnum(super().get_enum(input_str))

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
