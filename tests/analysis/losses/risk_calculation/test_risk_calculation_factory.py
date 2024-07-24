import pandas as pd

from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_factory import (
    RiskCalculationFactory,
)


class TestRiskCalculationFactory:
    def test_risk_calculation_factory(
        self,
        risk_calculation_info: tuple[RiskCalculationModeEnum, int],
        expected_factory_results: dict,
        losses: pd.DataFrame,
    ):
        _risk_calculation = RiskCalculationFactory.get_risk_calculation(
            risk_calculation_mode=risk_calculation_info[0],
            risk_calculation_year=risk_calculation_info[1],
            losses_gdf=losses,
        )

        assert isinstance(
            _risk_calculation,
            expected_factory_results[risk_calculation_info[0]]["class"],
        )
        assert sorted(_risk_calculation._return_periods) == sorted(
            expected_factory_results["_return_periods"]
        )
        pd.testing.assert_frame_equal(
            _risk_calculation._to_integrate,
            expected_factory_results[risk_calculation_info[0]]["_to_integrate"],
        )
