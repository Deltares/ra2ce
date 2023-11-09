from pathlib import Path
from typing import Optional

import pytest

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigDataWithNetwork,
)
from ra2ce.analyses.analysis_config_data.analysis_config_data_validator_with_network import (
    AnalysisConfigDataValidatorWithNetwork,
)
from ra2ce.common.validation.ra2ce_validator_protocol import Ra2ceIoValidator
from ra2ce.common.validation.validation_report import ValidationReport
from tests import test_data


class TestAnalysisConfigDataValidatorWithNetwork:
    def test_init_validator(self):
        _test_config_data = AnalysisConfigDataWithNetwork()
        _validator = AnalysisConfigDataValidatorWithNetwork(_test_config_data)
        assert isinstance(_validator, AnalysisConfigDataValidatorWithNetwork)
        assert isinstance(_validator, Ra2ceIoValidator)

    def test_validate_with_required_headers(self):
        _test_config_data = AnalysisConfigDataWithNetwork.from_dict({"project": {}})
        _validation_report = AnalysisConfigDataValidatorWithNetwork(
            _test_config_data
        ).validate()
        assert isinstance(_validation_report, ValidationReport)
        assert not _validation_report.is_valid()

    @pytest.mark.parametrize(
        "output_dict",
        [
            pytest.param(dict(), id="No output given"),
            pytest.param(dict(output=None), id="Output is none"),
            pytest.param(
                dict(output=(test_data / "not_a_path.ini")), id="Not a valid path."
            ),
        ],
    )
    def test_validate_without_output_reports_error(self, output_dict: dict):
        # 1. Define test data.
        _output_dir = output_dict.get("output_path", None)
        _expected_error = f"The configuration file 'network.ini' is not found at {_output_dir}.Please make sure to name your network settings file 'network.ini'."
        _test_config_data = AnalysisConfigDataWithNetwork.from_dict(
            {"project": {}} | output_dict
        )

        # 2. Run test.
        _validation_report = AnalysisConfigDataValidatorWithNetwork(
            _test_config_data
        ).validate()

        # 3. Verify expectations.
        assert isinstance(_validation_report, ValidationReport)
        assert not _validation_report.is_valid()
        assert _expected_error in _validation_report._errors
