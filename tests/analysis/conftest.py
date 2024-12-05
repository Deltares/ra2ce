import shutil
from pathlib import Path
from typing import Callable, Iterator

import pytest
from geopandas import GeoDataFrame
from shapely import Point

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionBase
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.analysis_result.analysis_result_wrapper import (
    AnalysisResult,
    AnalysisResultWrapper,
)


@pytest.fixture(name="single_analysis_result_wrapper")
def _get_single_analysis_result_wrapper_fixture() -> Iterator[AnalysisResultWrapper]:
    _analysis_result = AnalysisResult(
        analysis_result=GeoDataFrame.from_dict(dict(dummy=[(4.2, 2.4), (42, 24)])),
        analysis_config=None,
        output_path=None,
    )
    yield AnalysisResultWrapper(results_collection=[_analysis_result])


@pytest.fixture(name="analysis_result_builder")
def _get_analysis_result_builder_fixture() -> Iterator[
    Callable[[GeoDataFrame, AnalysisSectionBase, Path], AnalysisResult]
]:
    def create_analysis_result(
        gdf_result: GeoDataFrame,
        analysis_config: AnalysisSectionBase = None,
        output_path: Path = None,
    ) -> AnalysisResult:
        return AnalysisResult(
            analysis_result=gdf_result,
            analysis_config=analysis_config,
            output_path=output_path,
        )

    yield create_analysis_result


@pytest.fixture(name="mocked_analysis_result_wrapper")
def _get_valid_mocked_result_wrapper(
    test_result_param_case: Path,
    analysis_result_builder: Callable[[GeoDataFrame], AnalysisResult],
) -> Iterator[AnalysisResultWrapper]:
    class MockedAnalysis(AnalysisProtocol):
        def __init__(self) -> None:
            _analysis = AnalysisSectionBase(
                name="Mocked Analysis", save_csv=False, save_gpkg=False
            )
            _analysis.analysis = AnalysisLossesEnum.SINGLE_LINK_LOSSES
            self.analysis = _analysis
            self.output_path = test_result_param_case

    _result_gfd = GeoDataFrame(
        {
            "dummy_column": ["left", "right"],
            "geometry": [Point(4.2, 2.4), Point(42, 24)],
        }
    )

    _mocked_analysis = MockedAnalysis()
    _result_wrapper = AnalysisResultWrapper()
    _result_wrapper.results_collection.append(
        analysis_result_builder(
            gdf_result=_result_gfd,
            analysis_config=_mocked_analysis.analysis,
            output_path=_mocked_analysis.output_path,
        )
    )
    _single_result = _result_wrapper.results_collection[0]
    assert isinstance(_single_result, AnalysisResult)

    if _single_result.output_path.exists():
        shutil.rmtree(_single_result.output_path)
    return _result_wrapper
