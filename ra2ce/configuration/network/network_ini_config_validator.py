from ra2ce.configuration.validators.ini_config_validator_base import (
    IniConfigValidatorBase,
)
from ra2ce.validation.validation_report import ValidationReport


class NetworkIniConfigurationValidator(IniConfigValidatorBase):
    def _validate_shp_input(self, network_config: dict) -> ValidationReport:
        """Checks if a file id is configured when using the option to create network from shapefile"""
        _shp_report = ValidationReport()
        _source = network_config.get("source", None)
        _file_id = network_config.get("file_id", None)
        if (_source == "shapefile") and (not _file_id):
            _shp_report.error(
                "Not possible to create network - Shapefile used as source, but no file_id configured in the network.ini file"
            )
        return _shp_report

    def validate(self) -> ValidationReport:
        """Check if input properties are correct and exist."""
        _report = ValidationReport()
        _network_config = self._config.get("network", None)
        if not _network_config:
            _report.error("Network properties not present in Network ini file.")
            return _report

        # check if properties exist in settings.ini file
        _required_headers = [
            "project",
            "network",
            "origins_destinations",
            "hazard",
            "cleanup",
        ]
        _report.merge(self._validate_shp_input(_network_config))
        _report.merge(self._validate_headers(_required_headers))
        return _report
