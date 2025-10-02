from __future__ import annotations

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class EventTypeEnum(Ra2ceEnumBase):
    """
    Enumeration of event types for damage or risk analysis.

    This enum classifies the types of events that can be considered
    when analyzing road damages or risks. It is commonly used in
    conjunction with damage and risk calculations.

    Attributes
    ----------
    NONE : int
        No event specified (0).
    EVENT : int
        Calculate damages for separate events (1).
    RETURN_PERIOD : int
        Calculate damages for as risk taking into account return periods (2).
    INVALID : int
        Invalid or unsupported event type (99).
    """
    NONE = 0
    EVENT = 1
    RETURN_PERIOD = 2
    INVALID = 99

    @classmethod
    def get_enum(cls, input_str: str | None) -> EventTypeEnum:
        return EventTypeEnum(super().get_enum(input_str))
