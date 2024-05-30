import shutil

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionDamages,
    ProjectSection,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data_validator import (
    AnalysisConfigDataValidator,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.common.validation.ra2ce_validator_protocol import Ra2ceIoValidator
from ra2ce.common.validation.validation_report import ValidationReport
from tests import test_results


class TestAnalysisConfigDataValidator:
    def test_init_validator(self):
        # 1. Define test data.
        _test_config_data = AnalysisConfigData()

        # 2. Run test.
        _validator = AnalysisConfigDataValidator(_test_config_data)

        # 3. Verify expectations.
        assert isinstance(_validator, AnalysisConfigDataValidator)
        assert isinstance(_validator, Ra2ceIoValidator)

    def _validate_config(self, config_data: AnalysisConfigData) -> ValidationReport:
        _validator = AnalysisConfigDataValidator(config_data)
        return _validator.validate()

    def test_validate_with_required_headers(self, request: pytest.FixtureRequest):
        # 1. Define test data.
        _output_dir = test_results.joinpath(request.node.name)
        if _output_dir.exists():
            shutil.rmtree(_output_dir)
        _output_dir.mkdir(parents=True)

        # 2. Run test.
        _test_config_data = AnalysisConfigData(
            project=ProjectSection(),
            analyses=AnalysisSectionDamages(
                analysis=AnalysisDamagesEnum.DAMAGES,
                event_type=EventTypeEnum.EVENT,
                damage_curve=DamageCurveEnum.HZ,
            ),
            output_path=_output_dir,
        )
        _report = self._validate_config(_test_config_data)

        # 3. Verify expectations.
        assert _report.is_valid()

    def _validate_headers(
        self, config_data: AnalysisConfigData, required_headers: list[str]
    ) -> ValidationReport:
        _validator = AnalysisConfigDataValidator(config_data)
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

    def test_validate_headers_fails_when_invalid_value(self):
        # 1. Define test data.
        _test_config_data = AnalysisConfigData(
            root_path=test_results,
            output_path=test_results.joinpath("output"),
            project=ProjectSection(),
            analyses=[AnalysisSectionDamages(analysis="invalid_analysis_type")],
        )

        # 2. Run test.
        _report = self._validate_headers(
            _test_config_data, required_headers=["analyses"]
        )

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert len(_report._errors) == 4
