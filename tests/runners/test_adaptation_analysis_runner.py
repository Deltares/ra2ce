from pathlib import Path
from shutil import copytree, rmtree

from geopandas import read_file

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.enums.analysis_enum import AnalysisEnum
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_factory import AnalysisFactory
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.runners.adaptation_analysis_runner import AdaptationAnalysisRunner
from tests import test_data


class TestAdaptationAnalysisRunner:
    def test_init_adaptation_analysis_runner(self):
        _runner = AdaptationAnalysisRunner()
        assert str(_runner) == "Adaptation Analysis Runner"

    def test_given_wrong_analysis_configuration_cannot_run(
        self, dummy_analysis_collection: AnalysisCollection
    ):
        # 1. Define test data.
        _adaptation_analysis = dummy_analysis_collection.get_analysis(
            AnalysisEnum.ADAPTATION
        )
        assert not _adaptation_analysis

        # 2. Run test.
        _result = AdaptationAnalysisRunner().can_run(
            _adaptation_analysis, dummy_analysis_collection
        )

        # 3. Verify expectations.
        assert _result is False

    def test_given_valid_damages_and_adaptation_input_configuration_can_run(
        self, valid_analysis_collection: AnalysisCollection
    ):
        # 1. Define test data.
        _adaptation_analysis = valid_analysis_collection.get_analysis(
            AnalysisEnum.ADAPTATION
        )
        assert _adaptation_analysis

        # 2. Run test.
        _result = AdaptationAnalysisRunner().can_run(
            _adaptation_analysis, valid_analysis_collection
        )

        # 3. Verify expectation
        assert _result is True

    def test_adapatation_can_run_and_export_result(
        self,
        valid_analysis_config: AnalysisConfigWrapper,
        test_result_param_case: Path,
    ):
        # 1. Define test data.
        assert valid_analysis_config.config_data.adaptation

        _root_path = test_result_param_case
        valid_analysis_config.config_data._root_path = _root_path
        valid_analysis_config.config_data.input_path = _root_path.joinpath("input")
        valid_analysis_config.config_data._static_path = _root_path.joinpath("static")
        valid_analysis_config.config_data.output_path = _root_path.joinpath("output")

        # Copy input files for the adaptation analysis
        if _root_path.exists():
            rmtree(_root_path)
        valid_analysis_config.config_data.output_path.mkdir(parents=True)
        for _option in valid_analysis_config.config_data.adaptation.adaptation_options:
            _ao_path = valid_analysis_config.config_data.input_path.joinpath(_option.id)
            copytree(test_data.joinpath("adaptation", "input"), _ao_path)
        copytree(
            test_data.joinpath("adaptation", "static"),
            valid_analysis_config.config_data._static_pathstat,
        )

        # Read graph/network files
        valid_analysis_config.graph_files = GraphFilesCollection.set_files(
            valid_analysis_config.config_data._static_path.joinpath("output_graph"),
        )

        _analysis_collection = AnalysisCollection(
            damages_analyses=None,
            losses_analyses=None,
            adaptation_analysis=AnalysisFactory.get_adaptation_analysis(
                valid_analysis_config.config_data.adaptation, valid_analysis_config
            ),
        )

        # 2. Run test.
        _result = AdaptationAnalysisRunner().run(_analysis_collection)

        # 3. Verify expectation
        assert isinstance(_result, list)
        assert len(_result) == 1

        _result_wrapper = _result[0]
        assert isinstance(_result_wrapper, AnalysisResultWrapper)
        assert _result_wrapper.is_valid_result() is True

        _analysis_result = _result_wrapper.results_collection[0]
        _output_gdf = _analysis_result.base_export_path.with_suffix(".gpkg")
        assert _output_gdf.exists()
        assert _analysis_result.base_export_path.with_suffix(".csv").exists()

        # Check the output geodataframe content (columns might have different order)
        _gdf = read_file(_output_gdf)
        assert _gdf.shape == _analysis_result.analysis_result.shape
        assert all(
            _col in _gdf.columns for _col in _analysis_result.analysis_result.columns
        )
