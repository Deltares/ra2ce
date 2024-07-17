from typing import Iterator

import pandas as pd
import pytest

from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_factory import (
    RiskCalculationFactory,
)
from tests import test_data


class TestRiskCalculation:
    @pytest.fixture(
        params=[
            pytest.param(
                (RiskCalculationModeEnum.DEFAULT, 0),
                id=RiskCalculationModeEnum.DEFAULT.name.lower(),
            ),
            pytest.param(
                (RiskCalculationModeEnum.CUT_FROM_YEAR, 10000),
                id=RiskCalculationModeEnum.CUT_FROM_YEAR.name.lower(),
            ),
            pytest.param(
                (RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR, 0),
                id=RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR.name.lower(),
            ),
        ],
        name="risk_calculation_info",
    )
    def _get_risk_calculation_info(
        self, request: pytest.FixtureRequest
    ) -> Iterator[tuple[RiskCalculationModeEnum, int]]:
        _risk_calculation_info = request.param
        assert isinstance(_risk_calculation_info[0], RiskCalculationModeEnum)
        assert isinstance(_risk_calculation_info[1], int)
        yield _risk_calculation_info

    def test_risk_calculation_result(
        self, risk_calculation_info: tuple[RiskCalculationModeEnum, int]
    ):
        # 1. get the expected results
        _expected_result = pd.read_csv(
            test_data.joinpath(
                "losses", "csv_data_for_losses", "results_test_calc_vlh.csv"
            )
        )

        # 2. run
        _losses = _expected_result.drop(
            columns=[
                "EV1_ma",
                "EV2_mi",
                "vlh_business_EV1_ma",
                "vlh_commute_EV1_ma",
                "vlh_EV1_ma_total",
                "vlh_business_EV2_mi",
                "vlh_commute_EV2_mi",
                "vlh_EV2_mi_total",
                "risk_vlh_total_default",
                "risk_vlh_total_triangle_to_null_year",
                "risk_vlh_total_cut_from_year",
            ]
        )
        risk_calculation = RiskCalculationFactory.get_risk_calculation(
            risk_calculation_mode=risk_calculation_info[0],
            risk_calculation_year=risk_calculation_info[1],
            losses_gdf=_losses,
        )
        risk = risk_calculation.integrate_df_trapezoidal()
        _losses[f"risk_vlh_total_{risk_calculation_info[0].name.lower()}"] = risk

        # 3. Verify final expectations.
        pd.testing.assert_frame_equal(
            _losses[[f"risk_vlh_total_{risk_calculation_info[0].name.lower()}"]],
            _expected_result[
                [f"risk_vlh_total_{risk_calculation_info[0].name.lower()}"]
            ],
        )
