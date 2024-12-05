from __future__ import annotations

from enum import Enum


class Ra2ceEnumBase(Enum):
    """
    Base class for enums defined within Ra2ce.
    NONE = 0: Optional entry (config is optional and missing)
    INVALID = 99: Mandatory entry (config contains invalid value)
    """

    @classmethod
    def get_enum(cls, input_str: str | None) -> Ra2ceEnumBase:
        """
        Create an enum from a given input string.

        Args:
            input (str): Value from config.

        Returns:
            Ra2ceEnumBase: Enumeration instance.
            NONE: This entry is used if the config is missing.
            INVALID: This entry is used if the config value is invalid.
        """
        try:
            if not input_str:
                return cls.NONE
            return cls[input_str.upper().strip()]
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
        return True

    @classmethod
    def list_valid_options(cls) -> list[Ra2ceEnumBase]:
        """
        List the enum options as allowed in the config.

        Returns:
            list[str | None]: Concatenated options, separated by ", "
        """
        return [_enum for _enum in cls][:-1]

    def __str__(self) -> str:
        """
        Overwrite the default __str__

        Returns:
            str: Value as in the config
        """
        return str(self.config_value)

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
