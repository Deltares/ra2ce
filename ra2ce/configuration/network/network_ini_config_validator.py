from ra2ce.configuration.validators.ini_config_validator_base import (
    IniConfigValidatorBase,
)
from ra2ce.validation.validation_report import ValidationReport


class NetworkIniConfigurationValidator(IniConfigValidatorBase):
    def _validate_shp_input(self, network_config: dict) -> None:
        """Checks if a file id is configured when using the option to create network from shapefile"""
        if (network_config["source"] == "shapefile") and (
            network_config["file_id"] is None
        ):
            self._report.error(
                "Not possible to create network - Shapefile used as source, but no file_id configured in the network.ini file"
            )

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
        self._validate_shp_input(_network_config)
        _report.merge(self._validate_headers(_required_headers))
        return _report
