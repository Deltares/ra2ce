from typing import Any


class IniConfigDataProtocol(dict):
    """
    IniConfigProtocol, for now it's a dictionary until we start mapping its entries to real properties.
    Then we will transform it into a protocol.
    """

    @classmethod
    def from_dict(cls, dict_values) -> Any:
        pass

    def is_valid(self) -> bool:
        pass


class AnalysisIniConfigData(IniConfigDataProtocol):
    @classmethod
    def from_dict(cls, dict_values) -> IniConfigDataProtocol:
        _new_analysis_ini_config_data = cls()
        _new_analysis_ini_config_data.update(**dict_values)
        return _new_analysis_ini_config_data


class NetworkIniConfigData(IniConfigDataProtocol):
    @classmethod
    def from_dict(cls, dict_values) -> IniConfigDataProtocol:
        _new_network_ini_config_data = cls()
        _new_network_ini_config_data.update(**dict_values)
        return _new_network_ini_config_data
