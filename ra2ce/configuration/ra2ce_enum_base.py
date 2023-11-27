from __future__ import annotations

from enum import Enum


class Ra2ceEnumBase(Enum):
    """
    Base class for enums defined within Ra2ce.
    """

    @classmethod
    def get_enum(cls, input: str | None) -> Ra2ceEnumBase:
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
        except (AttributeError, KeyError):
            return cls.INVALID

    def is_valid(self) -> bool:
        """
        Check if given value is valid.

        Args:
            key (str): Enum key (name)

        Returns:
            bool: If the given key is not a valid key
        """
        if self.name == "INVALID":
            return False
        else:
            return True

    def list_valid_options(self) -> list[Ra2ceEnumBase]:
        """
        List the enum options as allowed in the config.

        Returns:
            list[str | None]: Concatenated options, separated by ", "
        """
        return [_enum for _enum in type(self)][:-1]

    def __str__(self) -> str:
        return self.name

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
        return self.name.lower()