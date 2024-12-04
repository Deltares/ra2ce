from pathlib import Path
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
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.network.network_config_data.network_config_data import (
    HazardSection,
    NetworkConfigData,
    NetworkSection,
)
from ra2ce.network.network_config_wrapper import NetworkConfigWrapper
from tests import test_data, test_results


class AdaptationOptionCases:
    """
    Test cases for the adaptation options.
    """

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
    unit_cost: list[float] = [0.0, 2693.684211, 5231.908660]
    total_cost: list[float] = [0.0, 633015.789583, 1229498.535112]
    cases: list[tuple[AnalysisSectionAdaptationOption, float, float]] = list(
        zip(config_cases, unit_cost, total_cost)
    )


@pytest.fixture(name="valid_adaptation_config")
def _get_valid_adaptation_config_fixture(
    request: pytest.FixtureRequest,
    valid_analysis_ini: Path,
) -> Iterator[tuple[AnalysisInputWrapper, AnalysisConfigWrapper]]:
    """
    Create valid input and config for the adaptation analysis.

    Args:
        request (pytest.FixtureRequest): Pytest fixture request.
        valid_analysis_ini (Path): Path to a valid analysis ini file.

    Yields:
        Iterator[tuple[AnalysisInputWrapper, AnalysisConfigWrapper]]:
            Tuple with the input and config for the adaptation analysis.
    """

    def get_losses_section(analysis: AnalysisLossesEnum) -> AnalysisSectionLosses:
        return AnalysisSectionLosses(
            analysis=analysis,
            event_type=EventTypeEnum.EVENT,
            weighing=WeighingEnum.TIME,
            threshold=0,
            production_loss_per_capita_per_hour=42,
            hours_per_traffic_period=8,
            traffic_period=TrafficPeriodEnum.DAY,
            trip_purposes=[
                TripPurposeEnum.BUSINESS,
                TripPurposeEnum.COMMUTE,
                TripPurposeEnum.FREIGHT,
                TripPurposeEnum.OTHER,
            ],
            resilience_curves_file=_input_path.joinpath("resilience_curves.csv"),
            traffic_intensities_file=_input_path.joinpath("traffic_intensities.csv"),
            values_of_time_file=_input_path.joinpath("values_of_time.csv"),
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
        copytree(
            test_data.joinpath("adaptation", "static"),
            _ao_path.joinpath("losses", "static"),
        )
    copytree(test_data.joinpath("adaptation", "static"), _static_path)

    # Create the config

    # - network
    _hazard_section = HazardSection(aggregate_wl=AggregateWlEnum.MEAN)
    _network_section = NetworkSection(
        file_id="ID",
        link_type_column="highway",
    )
    _network_config_data = NetworkConfigData(
        static_path=test_results.joinpath(request.node.name, "static"),
        hazard=_hazard_section,
        network=_network_section,
    )
    _network_config = NetworkConfigWrapper.from_data(None, _network_config_data)

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

    _analysis_data = AnalysisConfigData(
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
        aggregate_wl=AggregateWlEnum.MEAN,
    )

    _analysis_config = AnalysisConfigWrapper.from_data_with_network(
        valid_analysis_ini, _analysis_data, _network_config
    )

    _analysis_input = AnalysisInputWrapper.from_input(
        analysis=_analysis_config.config_data.adaptation,
        analysis_config=_analysis_config,
        graph_file=_analysis_config.graph_files.base_network,
        graph_file_hazard=_analysis_config.graph_files.base_network_hazard,
    )

    yield (_analysis_input, _analysis_config)
