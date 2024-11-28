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
from tests import test_results


@pytest.fixture(name="valid_adaptation_config")
def _get_valid_adaptation_config_fixture(
    request: pytest.FixtureRequest,
) -> Iterator[AnalysisConfigData]:
    _adaptation_options = ["AO0", "AO1", "AO2"]
    _root_path = test_results.joinpath(request.node.name, "adaptation")

    # TODO: create the input files

    # Damages
    _damages_section = AnalysisSectionDamages(
        analysis=AnalysisDamagesEnum.DAMAGES,
    )

    # Losses
    _losses_section = AnalysisSectionLosses(
        analysis=AnalysisLossesEnum.SINGLE_LINK_LOSSES,
        resilience_curves_file=_root_path.joinpath(
            "damage_functions", "resilience_curves.csv"
        ),
        traffic_intensities_file=_root_path.joinpath(
            "damage_functions", "traffic_intensities.csv"
        ),
        values_of_time_file=_root_path.joinpath(
            "damage_functions", "values_of_time.csv"
        ),
    )

    # Adaptation
    _adaptation_collection = []
    for i, _option in enumerate(_adaptation_options):
        _adaptation_collection.append(
            AnalysisSectionAdaptationOption(
                id=_option,
                name=f"Option {i}",
                construction_cost=1000.0,
                maintenance_interval=5.0,
                maintenance_cost=100.0,
            )
        )
    _adaptation_section = AnalysisSectionAdaptation(
        analysis=AnalysisEnum.ADAPTATION,
        losses_analysis=AnalysisLossesEnum.SINGLE_LINK_LOSSES,
        adaptation_options=_adaptation_collection,
    )

    yield AnalysisConfigData(
        root_path=_root_path,
        analyses=[_damages_section, _losses_section, _adaptation_section],
    )
