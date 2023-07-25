from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigDataWithNetwork,
)
from ra2ce.analyses.analysis_config_data.analysis_config_data_validator_with_network import (
    AnalysisConfigDataValidatorWithNetwork,
)
from ra2ce.common.validation.validation_report import ValidationReport


class TestAnalysisConfigDataValidatorWithNetwork:
    def test_init_validator(self):
        _test_config_data = AnalysisConfigDataWithNetwork()
        _validator = AnalysisConfigDataValidatorWithNetwork(_test_config_data)
        assert _validator

    def test_validate_with_required_headers(self):
        _test_config_data = AnalysisConfigDataWithNetwork.from_dict({"project": {}})
        _validation_report = AnalysisConfigDataValidatorWithNetwork(
            _test_config_data
        ).validate()
        assert isinstance(_validation_report, ValidationReport)
        assert _validation_report.is_valid()
