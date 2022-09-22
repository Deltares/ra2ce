from ra2ce.configuration.ini_config_protocol import IniConfigDataProtocol
from ra2ce.configuration.analysis.analysis_ini_config_validator import (
    AnalysisWithoutNetworkConfigValidator,
)


class AnalysisIniConfigData(IniConfigDataProtocol):
    @classmethod
    def from_dict(cls, dict_values) -> IniConfigDataProtocol:
        _new_analysis_ini_config_data = cls()
        _new_analysis_ini_config_data.update(**dict_values)
        return _new_analysis_ini_config_data

    def is_valid(self) -> bool:
        _validation_report = AnalysisWithoutNetworkConfigValidator(self).validate()
        return _validation_report.is_valid()
