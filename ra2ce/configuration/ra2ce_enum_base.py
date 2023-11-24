from __future__ import annotations

from enum import Enum


class Ra2ceEnumBase(Enum):
    """
    Base class for enums defined within Ra2ce.
    """

    @classmethod
    def get_enum(cls, input: str) -> Ra2ceEnumBase:
        """
        Create an enum from a given input string.

        Args:
            input (str): Value from config.

        Returns:
            Ra2ceEnumBase: Enumeration instance.
        """
        try:
            return cls[input.upper()]
        except KeyError:
            return cls.INVALID

    @property
    def config_value(self) -> str:
        """
        Reconstruct the name as it is known in the config.
        This could entail replacement of " " by "_" and lower() operations.

        Returns:
            str: Value as known in the config.
        """
        return self.name.lower()
