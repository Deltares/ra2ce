from shutil import copytree, rmtree
from typing import Iterator

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSectionAdaptation,
    AnalysisSectionAdaptationOption,
    AnalysisSectionDamages,
    AnalysisSectionLosses,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_enum import AnalysisEnum
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
from ra2ce.analysis.analysis_config_data.enums.traffic_period_enum import (
    TrafficPeriodEnum,
)
from ra2ce.analysis.analysis_config_data.enums.trip_purpose_enum import TripPurposeEnum
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from tests import test_data, test_results


class AdaptationOptionCases:
    config_cases: list[AnalysisSectionAdaptationOption] = [
        AnalysisSectionAdaptationOption(
            id="AO0",
            name="No adaptation",
        ),
        AnalysisSectionAdaptationOption(
            id="AO1",
            name="Cheap construction, expensive maintenance",
            construction_cost=1000.0,
            construction_interval=10.0,
            maintenance_cost=200.0,
            maintenance_interval=3.0,
        ),
        AnalysisSectionAdaptationOption(
            id="AO2",
            name="Expensive construction, cheap maintenance",
            construction_cost=5000.0,
            construction_interval=100.0,
            maintenance_cost=50.0,
            maintenance_interval=3.0,
        ),
    ]
    cost: list[float] = [0.0, 2693.684211, 5231.908660]
    cases = list(zip(config_cases, cost))


@pytest.fixture(name="valid_adaptation_config")
def _get_valid_adaptation_config_fixture(
    request: pytest.FixtureRequest,
) -> Iterator[AnalysisConfigData]:
    def get_losses_section(analysis: AnalysisLossesEnum) -> AnalysisSectionLosses:
        return AnalysisSectionLosses(
            analysis=analysis,
            event_type=EventTypeEnum.EVENT,
            weighing=WeighingEnum.TIME,
            threshold=0.5,
            production_loss_per_capita_per_hour=42,
            traffic_period=TrafficPeriodEnum.DAY,
            trip_purposes=[
                TripPurposeEnum.BUSINESS,
                TripPurposeEnum.COMMUTE,
                TripPurposeEnum.FREIGHT,
                TripPurposeEnum.OTHER,
            ],
            resilience_curves_file=_root_path.joinpath(
                "damage_functions", "resilience_curves.csv"
            ),
            traffic_intensities_file=_root_path.joinpath(
                "damage_functions", "traffic_intensities.csv"
            ),
            values_of_time_file=_root_path.joinpath(
                "damage_functions", "values_of_time.csv"
            ),
            save_gpkg=True,
            save_csv=True,
        )

    _root_path = test_results.joinpath(request.node.name)
    _input_path = _root_path.joinpath("input")
    _static_path = _root_path.joinpath("static")
    _output_path = _root_path.joinpath("output")

    # Create the input files
    if _root_path.exists():
        rmtree(_root_path)

    _input_path.mkdir(parents=True)
    for _option in AdaptationOptionCases.config_cases:
        _ao_path = _input_path.joinpath(_option.id)
        copytree(test_data.joinpath("adaptation", "input"), _ao_path)
    copytree(test_data.joinpath("adaptation", "static"), _static_path)

    # Create the config
    # - damages
    _damages_section = AnalysisSectionDamages(
        analysis=AnalysisDamagesEnum.DAMAGES,
        event_type=EventTypeEnum.EVENT,
        damage_curve=DamageCurveEnum.MAN,
        save_gpkg=True,
        save_csv=True,
    )
    # - losses
    _single_link_losses_section = get_losses_section(
        AnalysisLossesEnum.SINGLE_LINK_LOSSES
    )
    _multi_link_losses_section = get_losses_section(
        AnalysisLossesEnum.MULTI_LINK_LOSSES
    )
    # - adaptation
    _adaptation_section = AnalysisSectionAdaptation(
        analysis=AnalysisEnum.ADAPTATION,
        losses_analysis=AnalysisLossesEnum.MULTI_LINK_LOSSES,
        adaptation_options=AdaptationOptionCases.config_cases,
        discount_rate=0.025,
        time_horizon=20,
    )

    yield AnalysisConfigData(
        root_path=_root_path,
        input_path=_input_path,
        static_path=_static_path,
        output_path=_output_path,
        analyses=[
            _damages_section,
            _single_link_losses_section,
            _multi_link_losses_section,
            _adaptation_section,
        ],
    )
