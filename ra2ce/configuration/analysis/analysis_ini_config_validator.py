from ra2ce.configuration.validators.ini_config_validator_base import (
    IniConfigValidatorBase,
)
from ra2ce.validation.validation_report import ValidationReport


class AnalysisIniConfigValidator(IniConfigValidatorBase):
    def validate(self) -> ValidationReport:
        _report = ValidationReport()
        _required_headers = ["project"]
        # Analysis are marked as [analysis1], [analysis2], ...
        _required_headers.extend([a for a in self._config.keys() if "analysis" in a])

        _report.merge(self._validate_headers(_required_headers))
        return _report


class AnalysisWithoutNetworkConfigValidator(IniConfigValidatorBase):
    def validate(self) -> ValidationReport:
        _base_report = AnalysisIniConfigValidator(self._config).validate()
        _output_network_ini_file = self.config_data["output"] / "network.ini"

        if not _output_network_ini_file:
            _base_report.error(
                f"The configuration file 'network.ini' is not found at {_output_network_ini_file}."
                f"Please make sure to name your network settings file 'network.ini'."
            )
        return _base_report
