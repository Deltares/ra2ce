import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.damages_config_data import DamagesConfigData
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.common.validation.validation_report import ValidationReport


class TestDamagesConfigData:
    def test_initialize(self):
        # 1. Define test data.
        _data_name = "Test Damages Analysis"

        # 2. Run test.
        damages_config = DamagesConfigData(name=_data_name)

        # 3. Verify expectations.
        assert isinstance(damages_config, DamagesConfigData)
        assert isinstance(
            damages_config, AnalysisConfigDataProtocol
        )
        assert damages_config.name == _data_name
        assert damages_config.save_gpkg is False
        assert damages_config.save_csv is False

    @pytest.mark.parametrize(
        "risk_calculation_year",
        [
            pytest.param(None, id="none year"),
            pytest.param(-5, id="negative year"),
            pytest.param(0, id="zero year"),
        ],
    )
    def test_given_risk_calculation_triangle_and_invalid_year_when_validate_integrity_then_fails(
        self, risk_calculation_year: int | None
    ):
        # 1. Define test data.
        _data_name = "Invalid Damages Analysis"
        _damages_config = DamagesConfigData(
            name=_data_name,
            risk_calculation_mode=RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR,
            risk_calculation_year=risk_calculation_year,
        )

        _expected_error = f"For damage analysis '{_data_name}': 'risk_calculation_year' should be a positive integer when 'risk_calculation_mode' is set to 'RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR'."

        # 2. Run test.
        _report = _damages_config.validate_integrity()

        # 3. Verify expectations for invalid data.
        assert isinstance(_report, ValidationReport)
        assert (
            not _report.is_valid()
        ), "Expected invalid report due to negative risk_calculation_year"
        assert len(_report._errors) == 1
        assert _report._errors[0] == _expected_error

    def test_given_risk_calculation_triangle_and_valid_year_when_validate_integrity_then_succeeds(
        self,
    ):
        # 1. Define test data.
        _data_name = "Invalid Damages Analysis"
        _damages_config = DamagesConfigData(
            name=_data_name,
            risk_calculation_mode=RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR,
            risk_calculation_year=1,
        )

        # 2. Run test.
        _report = _damages_config.validate_integrity()

        # 3. Verify expectations for invalid data.
        assert isinstance(_report, ValidationReport)
        assert (
            _report.is_valid()
        ), "Expected valid report due to possitive risk_calculation_year"

    @pytest.mark.parametrize(
        "risk_calculation_mode",
        [
            pytest.param(_mode, id=_mode.name)
            for _mode in RiskCalculationModeEnum
            if _mode != RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR
        ],
    )
    @pytest.mark.parametrize("risk_calculation_year", [(None), (-5), (0), (2)])
    def test_given_any_non_triangle_risk_calculation_when_validate_integrity_then_succeeds(
        self,
        risk_calculation_mode: RiskCalculationModeEnum,
        risk_calculation_year: int | None,
    ):
        # 1. Define test data.
        _data_name = "Valid Damages Analysis"
        _damages_config = DamagesConfigData(
            name=_data_name,
            risk_calculation_mode=risk_calculation_mode,
            risk_calculation_year=risk_calculation_year,
        )

        # 2. Run test.
        _report = _damages_config.validate_integrity()

        # 3. Verify expectations for invalid data.
        assert isinstance(_report, ValidationReport)
        assert (
            _report.is_valid()
        ), "Expected valid report due to non-triangle risk calculation mode"
