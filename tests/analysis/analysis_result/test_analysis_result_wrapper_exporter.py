import pytest

from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.analysis.analysis_result.analysis_result_wrapper_exporter import (
    AnalysisResultWrapperExporter,
)


class TestAnalysisResultWrapperExporter:
    def test_initialize(self):
        _exporter = AnalysisResultWrapperExporter()
        assert isinstance(_exporter, AnalysisResultWrapperExporter)

    def test_given_invalid_result_doesnot_raise(self):
        # 1. Define test data
        _exporter = AnalysisResultWrapperExporter()
        _result_wrapper = AnalysisResultWrapper(results_collection=[])
        assert _result_wrapper.is_valid_result() is False

        # 2. Run test
        _exporter.export_result(_result_wrapper)

    @pytest.mark.parametrize(
        "save_gpkg",
        [pytest.param(True, id="WITH gpkg"), pytest.param(False, id="WITHOUT gpkg")],
    )
    @pytest.mark.parametrize(
        "save_csv",
        [pytest.param(True, id="WITH csv"), pytest.param(False, id="WITHOUT csv")],
    )
    def test_given_export_properties_then_generates_files(
        self,
        save_gpkg: bool,
        save_csv: bool,
        mocked_analysis_result_wrapper: AnalysisResultWrapper,
    ):
        # 1. Define test data.
        _single_result = mocked_analysis_result_wrapper.results_collection[0]
        _single_result.analysis_config.save_gpkg = save_gpkg
        _single_result.analysis_config.save_csv = save_csv
        _exporter = AnalysisResultWrapperExporter()

        assert _single_result.output_path.exists() is False
        assert mocked_analysis_result_wrapper.is_valid_result()

        # 2. Run test.
        _exporter.export_result(mocked_analysis_result_wrapper)

        # 3. Verify expectations
        def exists_exported_file(extension: str) -> bool:
            return _single_result.base_export_path.with_suffix(extension).is_file()

        assert exists_exported_file(".csv") == save_csv
        assert exists_exported_file(".gpkg") == save_gpkg
