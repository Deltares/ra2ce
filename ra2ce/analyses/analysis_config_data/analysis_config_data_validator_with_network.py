from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigDataWithNetwork,
)
from ra2ce.analyses.analysis_config_data.analysis_config_data_validator import (
    AnalysisConfigDataValidatorWithoutNetwork,
)
from ra2ce.common.validation.ra2ce_validator_protocol import Ra2ceIoValidator
from ra2ce.common.validation.validation_report import ValidationReport


class AnalysisConfigDataValidatorWithNetwork(Ra2ceIoValidator):
    def __init__(self, config_data: AnalysisConfigDataWithNetwork) -> None:
        self._config = config_data

    def validate(self) -> ValidationReport:
        _base_report = AnalysisConfigDataValidatorWithoutNetwork(
            self._config
        ).validate()
        _output_network_dir = self._config.get("output", None)
        if (
            not _output_network_dir
            or not (_output_network_dir / "network.ini").is_file()
        ):
            _base_report.error(
                f"The configuration file 'network.ini' is not found at {_output_network_dir}."
                f"Please make sure to name your network settings file 'network.ini'."
            )
        return _base_report
