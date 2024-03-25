import shutil
import pytest
import geopandas as gpd
from shapely import Point
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionBase
from ra2ce.analysis.analysis_config_data.enums.analysis_indirect_enum import (
    AnalysisIndirectEnum,
)
from ra2ce.analysis.analysis_protocol import AnalysisProtocol
from ra2ce.analysis.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.analysis_result_wrapper_exporter import (
    AnalysisResultWrapperExporter,
)
from tests import test_results


class TestAnalysisResultWrapperExporter:

    def test_initialize(self):
        _exporter = AnalysisResultWrapperExporter()
        assert isinstance(_exporter, AnalysisResultWrapperExporter)

    def test_given_invalid_result_doesnot_raise(self):
        # 1. Define test data
        _exporter = AnalysisResultWrapperExporter()
        _result_wrapper = AnalysisResultWrapper(analysis=None, analysis_result=None)
        assert _result_wrapper.is_valid_result() is False

        # 2. Run test
        _exporter.export_result(_result_wrapper)

    @pytest.fixture
    def valid_result_wrapper(
        self, request: pytest.FixtureRequest
    ) -> AnalysisResultWrapper:
        class MockedAnalysis(AnalysisProtocol):
            def __init__(self) -> None:
                _analysis = AnalysisSectionBase(
                    name="Mocked Analysis", save_csv=False, save_gpkg=False
                )
                _analysis.analysis = AnalysisIndirectEnum.SINGLE_LINK_LOSSES
                self.analysis = _analysis
                self.output_path = test_results.joinpath(request.node.name)

        _result_gfd = gpd.GeoDataFrame(
            {
                "dummy_column": ["left", "right"],
                "geometry": [Point(4.2, 2.4), Point(42, 24)],
            }
        )

        _result_wrapper = AnalysisResultWrapper(
            analysis=MockedAnalysis(), analysis_result=_result_gfd
        )

        if _result_wrapper.analysis.output_path.exists():
            shutil.rmtree(_result_wrapper.analysis.output_path)
        return _result_wrapper

    def _export_valid_result_to_expected_format(
        self, wrapper: AnalysisResultWrapper, extension: str
    ):
        # 1. Define test data.
        _exporter = AnalysisResultWrapperExporter()

        assert wrapper.analysis.output_path.exists() is False
        assert wrapper.is_valid_result()

        # 2. Run test.
        _exporter.export_result(wrapper)

        # 3. Verify expectations
        assert wrapper.analysis.output_path.exists()
        _result_files = list(wrapper.analysis.output_path.rglob(f"*.{extension}"))
        assert any(_result_files)

    def test_given_valid_result_export_gdf(
        self, valid_result_wrapper: AnalysisResultWrapper
    ):
        # 1. Define test data.
        valid_result_wrapper.analysis.analysis.save_gpkg = True
        self._export_valid_result_to_expected_format(valid_result_wrapper, "gpkg")

    def test_given_valid_result_export_csv(
        self, valid_result_wrapper: AnalysisResultWrapper
    ):
        # 1. Define test data.
        valid_result_wrapper.analysis.analysis.save_csv = True
        self._export_valid_result_to_expected_format(valid_result_wrapper, "csv")
