from ra2ce.configuration.ini_config_protocol import IniConfigDataProtocol
from ra2ce.configuration.network.network_ini_config_validator import (
    NetworkIniConfigurationValidator,
)


class NetworkIniConfigData(IniConfigDataProtocol):
    @classmethod
    def from_dict(cls, dict_values) -> IniConfigDataProtocol:
        _new_network_ini_config_data = cls()
        _new_network_ini_config_data.update(**dict_values)
        return _new_network_ini_config_data

    def is_valid(self) -> bool:
        _report = NetworkIniConfigurationValidator(self).validate()
        return _report.is_valid()
