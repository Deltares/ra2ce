from pathlib import Path
from typing import Optional

import pytest

from ra2ce.configuration.analysis.analysis_ini_config_data import (
    AnalysisWithNetworkIniConfigData,
    AnalysisWithoutNetworkIniConfigData,
)
from ra2ce.configuration.analysis.analysis_ini_config_validator import (
    AnalysisIniConfigValidator,
    AnalysisWithoutNetworkConfigValidator,
)
from ra2ce.validation.validation_report import ValidationReport
from tests import test_data


class TestAnalysisIniConfigValidator:
    def _validate_from_dict(self, dict_values: dict) -> ValidationReport:
        _test_config_data = AnalysisWithNetworkIniConfigData.from_dict(dict_values)
        _validator = AnalysisIniConfigValidator(_test_config_data)
        return _validator.validate()

    def test_init_validator(self):
        _test_config_data = AnalysisWithNetworkIniConfigData()
        _validator = AnalysisIniConfigValidator(_test_config_data)
        assert _validator

    def test_validate_with_required_headers(self):
        _test_config_data = {"project": {}}
        _validator = self._validate_from_dict(_test_config_data)
        assert _validator.is_valid()


class TestAnalysisWithoutNetworkConfigValidator:
    def _validate_from_dict(self, dict_values: dict) -> ValidationReport:
        _test_config_data = AnalysisWithoutNetworkIniConfigData.from_dict(dict_values)
        _validator = AnalysisWithoutNetworkConfigValidator(_test_config_data)
        return _validator.validate()

    def test_validate_with_required_headers(self):
        # 1. Define test data.
        _output_test_dir = test_data / "acceptance_test_data"
        assert _output_test_dir.is_dir()

        # 2. Run test.
        _test_config_data = {"project": {}, "output": _output_test_dir}
        _report = self._validate_from_dict(_test_config_data)

        # 3. Verify expectations.
        assert _report.is_valid()

    @pytest.mark.parametrize(
        "output_entry",
        [
            pytest.param(dict(), id="No output given"),
            pytest.param(dict(output=None), id="Output is none"),
            pytest.param(
                dict(output=(test_data / "not_a_path.ini")), id="Not a valid path."
            ),
        ],
    )
    def test_validate_withoutput_output_reports_error(
        self, output_entry: Optional[Path]
    ):
        # 1. Define test data.
        _output_dir = output_entry.get("output", None)
        _expected_error = f"The configuration file 'network.ini' is not found at {_output_dir}.Please make sure to name your network settings file 'network.ini'."
        _test_config_data = {"project": {}}
        _test_config_data.update(output_entry)

        # 2. Run test.
        _report = self._validate_from_dict(_test_config_data)

        # 3. Verify expectations.
        assert not _report.is_valid()
        assert _expected_error in _report._errors
