import pandas as pd
from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_factory import (
    RiskCalculationFactory,
)
from tests import test_data


class TestRiskCalculation:
    def test_risk_calculation_result(
        self,
        risk_calculation_info: tuple[RiskCalculationModeEnum, int],
        losses_fixture: pd.DataFrame,
    ):
        # 1. get the expected results
        _expected_result = pd.read_csv(
            test_data.joinpath(
                "losses", "csv_data_for_losses", "results_test_calc_vlh.csv"
            )
        )

        # 2. run
        risk_calculation = RiskCalculationFactory.get_risk_calculation(
            risk_calculation_mode=risk_calculation_info[0],
            risk_calculation_year=risk_calculation_info[1],
            losses_gdf=losses_fixture,
        )
        risk = risk_calculation.integrate_df_trapezoidal()
        losses_fixture[f"risk_vlh_total_{risk_calculation_info[0].name.lower()}"] = risk

        # 3. Verify final expectations.
        pd.testing.assert_frame_equal(
            losses_fixture[[f"risk_vlh_total_{risk_calculation_info[0].name.lower()}"]],
            _expected_result[
                [f"risk_vlh_total_{risk_calculation_info[0].name.lower()}"]
            ],
            rtol=1e-0,
            atol=1e-2,
        )
