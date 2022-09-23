from __future__ import annotations

from typing import Any


class IniConfigDataProtocol(dict):
    """
    IniConfigProtocol, for now it's a dictionary until we start mapping its entries to real properties.
    Then we will transform it into a protocol.
    """

    @classmethod
    def from_dict(cls, dict_values: dict) -> IniConfigDataProtocol:
        """
        Initializes the `IniConfigDataProtocol` concrete class based on the given values.

        Args:
            dict_values (dict): Dictionary of values to map into the `IniConfigDataProtocol`

        Returns:
            IniConfigDataProtocol:  Initialized object.
        """
        pass

    def is_valid(self) -> bool:
        """
        Validates the current instance.

        Returns:
            bool: Whether it is valid or not.
        """
        pass
