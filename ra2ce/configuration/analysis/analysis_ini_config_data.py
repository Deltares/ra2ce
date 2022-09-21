from ra2ce.configuration.ini_config_protocol import IniConfigDataProtocol


class AnalysisIniConfigData(IniConfigDataProtocol):
    @classmethod
    def from_dict(cls, dict_values) -> IniConfigDataProtocol:
        _new_analysis_ini_config_data = cls()
        _new_analysis_ini_config_data.update(**dict_values)
        return _new_analysis_ini_config_data
