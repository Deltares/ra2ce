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
from ra2ce.analysis.losses.risk_calculation.risk_calculation_triangle_to_null_year import (
    RiskCalculationTriangleToNullYear,
)
from tests import test_data


@pytest.fixture(name="losses_fixture")
def get_losses_fixture() -> Iterator[pd.DataFrame]:
    _csv_results_filepath = test_data.joinpath(
        "losses", "csv_data_for_losses", "results_test_calc_vlh.csv"
    )
    assert _csv_results_filepath.exists()
    _test_calc_vlh = pd.read_csv(_csv_results_filepath)
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


@pytest.fixture(name="expected_factory_results_fixture")
def get_expected_factory_results_fixture() -> Iterator[dict]:
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
        "_return_periods": {100, 1000},
    }
    yield _expected_factory_results


@pytest.fixture(
    params=[
        pytest.param(
            (RiskCalculationModeEnum.DEFAULT, 0),
            id=RiskCalculationModeEnum.DEFAULT.name,
        ),
        pytest.param(
            (RiskCalculationModeEnum.CUT_FROM_YEAR, 500),
            id=RiskCalculationModeEnum.CUT_FROM_YEAR.name,
        ),
        pytest.param(
            (RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR, 0),
            id=RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR.name,
        ),
    ],
    name="risk_calculation_info_fixture",
)
def _get_risk_calculation_info_fixture(
    request: pytest.FixtureRequest,
) -> Iterator[tuple[RiskCalculationModeEnum, int]]:
    _risk_calculation_info = request.param
    assert isinstance(_risk_calculation_info[0], RiskCalculationModeEnum)
    assert isinstance(_risk_calculation_info[1], int)
    yield _risk_calculation_info
