from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.common.validation.validation_report import ValidationReport


def validate_risk_calculation(func) -> ValidationReport:
    """
    Validates the risk calculation settings of a config data instance.
    Risk calculation year is required and greater than 0 if 'risk_calculation_mode' is set to 'RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR'.

    Args:
        func (Callable): The integrity validation method to be wrapped.

    Returns:
        ValidationReport: The validation report.
    """
    def wrapper(self) -> ValidationReport:
        _report = func(self)
        if self.risk_calculation_mode == RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR:
            if self.risk_calculation_year is None or self.risk_calculation_year <= 0:
                _report.error(
                    f"For damage analysis '{self.name}': 'risk_calculation_year' should be a positive integer when 'risk_calculation_mode' is set to 'RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR'."
                )
        _report.merge(func(self))
        return _report
    return wrapper