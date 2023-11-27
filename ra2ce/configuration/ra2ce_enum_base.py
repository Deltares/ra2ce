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
            if not input:
                return cls.NONE
            return cls[input.upper()]
        except KeyError:
            return cls.INVALID

    @classmethod
    def is_valid(cls, enum: Ra2ceEnumBase | None) -> bool:
        """
        Check if given value is valid.

        Args:
            key (str): Enum key (name)

        Returns:
            bool: If the given key is not a valid key
        """
        if enum is None:
            if hasattr(cls, "NONE"):
                return True
            else:
                return False
        elif enum.name == "INVALID":
            return False
        else:
            return True

    @property
    def config_value(self) -> str:
        """
        Reconstruct the name as it is known in the config.
        This could entail replacement of " " by "_" and lower() operations.

        Returns:
            str: Value as known in the config.
        """
        if self.name == "NONE":
            return None
        return self.name.lower()
