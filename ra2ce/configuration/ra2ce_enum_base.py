from __future__ import annotations

from enum import Enum


class Ra2ceEnumBase(Enum):
    """
    Acts as protocol for enums defined within Ra2ce.
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
        pass

    @property
    def config_value(self) -> str:
        """
        Reconstruct the name as it is known in the config.
        This could entain replacement of " " by "_" and lower() operations.

        Returns:
            str: Value as known in the config.
        """
        pass
