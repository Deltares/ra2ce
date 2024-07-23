from typing import Iterator
import numpy as np
import pandas as pd
import pytest

from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import (
    RiskCalculationModeEnum,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_cut_from_year import (
    RiskCalculationCutFromYear,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_default import (
    RiskCalculationDefault,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_factory import (
    RiskCalculationFactory,
)
from ra2ce.analysis.losses.risk_calculation.risk_calculation_triangle_to_null_year import (
    RiskCalculationTriangleToNullYear,
)
from tests import test_data


@pytest.fixture(
    params=[
        pytest.param(
            (RiskCalculationModeEnum.DEFAULT, 0),
            id=RiskCalculationModeEnum.DEFAULT.name.lower(),
        ),
        pytest.param(
            (RiskCalculationModeEnum.CUT_FROM_YEAR, 500),
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
    request: pytest.FixtureRequest,
) -> Iterator[tuple[RiskCalculationModeEnum, int]]:
    _risk_calculation_info = request.param
    assert isinstance(_risk_calculation_info[0], RiskCalculationModeEnum)
    assert isinstance(_risk_calculation_info[1], int)
    yield _risk_calculation_info


@pytest.fixture(name="_losses")
def get_losses() -> pd.DataFrame:
    assert test_data.joinpath(
        "losses", "csv_data_for_losses", "results_test_calc_vlh.csv"
    ).exists()

    _test_calc_vlh = pd.read_csv(
        test_data.joinpath("losses", "csv_data_for_losses", "results_test_calc_vlh.csv")
    )
    yield _test_calc_vlh.drop(
        columns=[
            "EV1_ma",
            "EV2_mi",
            "vlh_business_EV1_ma",
            "vlh_commute_EV1_ma",
            "vlh_business_EV2_mi",
            "vlh_commute_EV2_mi",
            "risk_vlh_total_default",
            "risk_vlh_total_triangle_to_null_year",
            "risk_vlh_total_cut_from_year",
        ]
    )


@pytest.fixture(name="_expected_factory_results")
def get_expected_factory_results() -> dict:
    _expected_factory_results = {
        RiskCalculationModeEnum.DEFAULT: {
            "class": RiskCalculationDefault,
            "_to_integrate": pd.DataFrame(
                [
                    [5.869500e06] * 3,
                    [2.540240e05] * 3,
                    [1.2899164e06] * 3,
                    [2.2945832e06] * 3,
                    [1.459500e06] * 3,
                    [2.533333e02] * 3,
                ],
                columns=[1000, 100, np.inf],
            ),
        },
        RiskCalculationModeEnum.CUT_FROM_YEAR: {
            "class": RiskCalculationCutFromYear,
            "_to_integrate": pd.DataFrame(
                [
                    [5.869500e06] * 3,
                    [2.540240e05] * 3,
                    [1.2899164e06] * 3,
                    [2.2945832e06] * 3,
                    [1.459500e06] * 3,
                    [2.533333e02] * 3,
                ],
                columns=[np.inf, 1000, 500],
            ),
        },
        RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR: {
            "class": RiskCalculationTriangleToNullYear,
            "_to_integrate": pd.DataFrame(
                [
                    [5.869500e06] * 3 + [0],
                    [2.540240e05] * 3 + [0],
                    [1.2899164e06] * 3 + [0],
                    [2.2945832e06] * 3 + [0],
                    [1.459500e06] * 3 + [0],
                    [2.533333e02] * 3 + [0],
                ],
                columns=[np.inf, 1000, 100, 1],
            ),
        },
        "return_periods": {100, 1000},
    }
    yield _expected_factory_results


class TestRiskCalculationFactory:

    def test_risk_calculation_factory(
        self,
        risk_calculation_info: tuple[RiskCalculationModeEnum, int],
        _expected_factory_results: dict,
        _losses: pd.DataFrame,
    ):
        _risk_calculation = RiskCalculationFactory.get_risk_calculation(
            risk_calculation_mode=risk_calculation_info[0],
            risk_calculation_year=risk_calculation_info[1],
            losses_gdf=_losses,
        )

        assert isinstance(
            _risk_calculation,
            _expected_factory_results[risk_calculation_info[0]]["class"],
        )
        assert sorted(_risk_calculation.return_periods) == sorted(
            _expected_factory_results["return_periods"]
        )
        pd.testing.assert_frame_equal(
            _risk_calculation._to_integrate,
            _expected_factory_results[risk_calculation_info[0]]["_to_integrate"],
        )


class TestRiskCalculation:
    def test_risk_calculation_result(
        self,
        risk_calculation_info: tuple[RiskCalculationModeEnum, int],
        _losses: pd.DataFrame,
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
            rtol=1e-0,
            atol=1e-2,
        )
