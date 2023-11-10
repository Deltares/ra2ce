from pathlib import Path
from typing import Optional

import pytest

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisConfigDataWithoutNetwork,
    AnalysisSectionDirect,
    ProjectSection,
)
from ra2ce.analyses.analysis_config_data.analysis_config_data_validator_without_network import (
    AnalysisConfigDataValidatorWithoutNetwork,
)
from ra2ce.common.validation.validation_report import ValidationReport
from tests import test_data, test_results


class TestAnalysisConfigDataValidatorWithoutNetwork:
    def _validate_config(self, config_data: AnalysisConfigData) -> ValidationReport:
        _validator = AnalysisConfigDataValidatorWithoutNetwork(config_data)
        return _validator.validate()

    def test_validate_with_required_headers(self):
        # 1. Define test data.
        _output_test_dir = test_data.joinpath("acceptance_test_data")
        assert _output_test_dir.is_dir()

        # 2. Run test.
        _test_config_data = AnalysisConfigData(
            project=None, output_path=_output_test_dir
        )
        _report = self._validate_config(_test_config_data)

        # 3. Verify expectations.
        assert _report.is_valid()

    def test_validate_files_no_path_value_list_returns_empty_report(self):
        # 1. Define test data.
        _validator = AnalysisConfigDataValidatorWithoutNetwork(
            AnalysisConfigDataWithoutNetwork()
        )

        # 2. Run test.
        _report = _validator._validate_files("does_not_matter", [])

        # 3. Verify expectations.
        assert isinstance(_report, ValidationReport)
        assert _report.is_valid()

    def test_validate_files_with_non_existing_files_reports_error(self):
        # 1. Define test data.
        _validator = AnalysisConfigDataValidatorWithoutNetwork(
            AnalysisConfigDataWithoutNetwork()
        )
        _test_file = test_data / "not_a_valid_file.txt"

        # 2. Run test.
        _report = _validator._validate_files("dummy_header", [_test_file])

        # 3. Verify expectations.
        assert isinstance(_report, ValidationReport)
        assert not _report.is_valid()
        assert len(_report._errors) == 2

    def test_validate_road_types_no_road_type_returns_empty_report(self):
        # 1. Define test data.
        _validator = AnalysisConfigDataValidatorWithoutNetwork(
            AnalysisConfigDataWithoutNetwork()
        )

        # 2. Run test.
        _report = _validator._validate_road_types("")

        # 3. Verify expectations.
        assert isinstance(_report, ValidationReport)
        assert _report.is_valid()

    def test_validate_road_types_with_unexpected_road_type_reports_error(self):
        # 1. Define test data.
        _validator = AnalysisConfigDataValidatorWithoutNetwork(
            AnalysisConfigDataWithoutNetwork()
        )
        _road_type = "not a valid road type"

        # 2. Run test.
        _report = _validator._validate_road_types(_road_type)

        # 3. Verify expectations.
        assert isinstance(_report, ValidationReport)
        assert not _report.is_valid()
        assert len(_report._errors) == 1

    def _validate_headers(
        self, config_data: AnalysisConfigData, required_headers: list[str]
    ) -> ValidationReport:
        _validator = AnalysisConfigDataValidatorWithoutNetwork(config_data)
        return _validator._validate_headers(required_headers)

    def test_validate_headers_fails_when_missing_expected_header(self):
        # 1. Define test data.
        _test_config_data = AnalysisConfigData()
        _missing_header = "Deltares"
        _expected_err = f"Property [ {_missing_header} ] is not configured. Add property [ {_missing_header} ] to the *.ini file. "

        # 2. Run test.
        _report = self._validate_headers(
            _test_config_data, required_headers=[_missing_header]
        )

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert _expected_err in _report._errors

    def test_validate_headers_fails_when_invalid_value(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        _test_config_data = AnalysisConfigData(
            root_path=test_results,
            project=ProjectSection(name=request.node.name),
            direct=[AnalysisSectionDirect(analysis="invalid_analysis_type")],
        )

        # 2. Run test.
        _report = self._validate_headers(_test_config_data, required_headers=["direct"])

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert len(_report._errors) == 2
