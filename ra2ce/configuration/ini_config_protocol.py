from typing import Any


class IniConfigDataProtocol(dict):
    """
    IniConfigProtocol, for now it's a dictionary until we start mapping its entries to real properties.
    Then we will transform it into a protocol.
    """

    @classmethod
    def from_dict(cls, dict_values: dict) -> Any:
        pass


class AnalysisIniConfigData(IniConfigDataProtocol):
    pass


class NetworkIniConfigData(IniConfigDataProtocol):
    pass
