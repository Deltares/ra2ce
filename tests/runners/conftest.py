from pathlib import Path
from typing import Iterator

import pytest
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_collection import AnalysisCollection
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
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.network.graph_files.graph_file import GraphFile
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection


class DummyAnalysisConfigWrapper(AnalysisConfigWrapper):
    def __init__(self) -> None:
        self.config_data = AnalysisConfigData(
            analyses=[],
            root_path=Path("dummy"),
            input_path=Path("dummy/input"),
        )
        self.graph_files = GraphFilesCollection()

    @classmethod
    def from_data(cls, **kwargs):
        raise NotImplementedError()

    def configure(self) -> None:
        raise NotImplementedError()

    def is_valid(self) -> bool:
        raise NotImplementedError()


@pytest.fixture(name="valid_analysis_config")
def _get_valid_analysis_config_fixture() -> Iterator[AnalysisConfigWrapper]:
    _analysis_config = DummyAnalysisConfigWrapper()
    assert isinstance(_analysis_config, AnalysisConfigWrapper)
    _analysis_config.config_data.analyses = [
        AnalysisSectionDamages(
            analysis=AnalysisDamagesEnum.DAMAGES,
            name="Damages",
            event_type=EventTypeEnum.EVENT,
            damage_curve=DamageCurveEnum.HZ,
            save_csv=True,
            save_gpkg=True,
        ),
        AnalysisSectionLosses(analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY),
        AnalysisSectionLosses(analysis=AnalysisLossesEnum.MULTI_LINK_REDUNDANCY),
        AnalysisSectionAdaptation(
            analysis=AnalysisEnum.ADAPTATION,
            name="Adaptation",
            adaptation_options=[
                AnalysisSectionAdaptationOption(id="AO0"),
            ],
            save_csv=True,
            save_gpkg=True,
        ),
    ]
    yield _analysis_config


@pytest.fixture(name="dummy_analysis_collection")
def _get_dummy_analysis_collection_fixture() -> Iterator[AnalysisCollection]:
    _analysis_config = DummyAnalysisConfigWrapper()
    assert isinstance(_analysis_config, AnalysisConfigWrapper)
    yield AnalysisCollection.from_config(_analysis_config)


@pytest.fixture(name="valid_analysis_collection")
def _get_valid_analysis_collection_fixture(
    valid_analysis_config: AnalysisConfigWrapper,
) -> Iterator[AnalysisCollection]:
    _analysis_collection = AnalysisCollection.from_config(valid_analysis_config)
    _analysis_collection.damages_analyses[0].graph_file_hazard = GraphFile(
        graph=GeoDataFrame()
    )
    yield _analysis_collection
