from ra2ce.configuration.ini_config_protocol import IniConfigDataProtocol


class NetworkIniConfigData(IniConfigDataProtocol):
    @classmethod
    def from_dict(cls, dict_values) -> IniConfigDataProtocol:
        _new_network_ini_config_data = cls()
        _new_network_ini_config_data.update(**dict_values)
        return _new_network_ini_config_data
