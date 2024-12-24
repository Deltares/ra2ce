from pathlib import Path
from shutil import copytree, rmtree

from geopandas import read_file
from geopandas.testing import assert_geodataframe_equal

from ra2ce.analysis.analysis_collection import AnalysisCollection
from ra2ce.analysis.analysis_config_data.analysis_config_data import (
    AnalysisSectionAdaptation,
    AnalysisSectionAdaptationOption,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_enum import AnalysisEnum
from ra2ce.analysis.analysis_factory import AnalysisFactory
from ra2ce.analysis.analysis_result.analysis_result_wrapper import AnalysisResultWrapper
from ra2ce.configuration.config_wrapper import ConfigWrapper
from ra2ce.network.graph_files.graph_files_collection import GraphFilesCollection
from ra2ce.runners.adaptation_analysis_runner import AdaptationAnalysisRunner
from tests import test_data


class TestAdaptationAnalysisRunner:
    def test_init_adaptation_analysis_runner(self):
        _runner = AdaptationAnalysisRunner()
        assert str(_runner) == "Adaptation Analysis Runner"

    def test_given_wrong_analysis_configuration_cannot_run(
        self, dummy_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        assert dummy_ra2ce_input.analysis_config.config_data.adaptation is None

        # 2. Run test.
        _result = AdaptationAnalysisRunner.can_run(dummy_ra2ce_input)

        # 3. Verify expectations.
        assert not _result

    def test_given_valid_damages_input_configuration_cannot_run(
        self, damages_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        assert damages_ra2ce_input.analysis_config.config_data.adaptation is None

        # 2. Run test.
        _result = AdaptationAnalysisRunner.can_run(damages_ra2ce_input)

        # 3. Verify expectation
        assert _result is False

    def test_given_valid_damages_and_adaptation_input_configuration_can_run(
        self, damages_ra2ce_input: ConfigWrapper
    ):
        # 1. Define test data.
        assert damages_ra2ce_input.analysis_config.config_data.adaptation is None
        _adaptation_config = AnalysisSectionAdaptation()
        _adaptation_config.adaptation_options = [
            AnalysisSectionAdaptationOption(id="AO0"),
            AnalysisSectionAdaptationOption(id="AO1"),
            AnalysisSectionAdaptationOption(id="AO2"),
        ]
        damages_ra2ce_input.analysis_config.config_data.analyses.append(
            _adaptation_config
        )

        # 2. Run test.
        _result = AdaptationAnalysisRunner.can_run(damages_ra2ce_input)

        # 3. Verify expectation
        assert _result is True

    def test_adapatation_can_run_and_export_result(
        self,
        damages_ra2ce_input: ConfigWrapper,
        test_result_param_case: Path,
    ):
        # 1. Define test data.
        assert damages_ra2ce_input.analysis_config.config_data.adaptation is None

        _root_path = test_result_param_case
        damages_ra2ce_input.analysis_config.config_data.root_path = _root_path
        damages_ra2ce_input.analysis_config.config_data.input_path = (
            _root_path.joinpath("input")
        )
        damages_ra2ce_input.analysis_config.config_data.static_path = (
            _root_path.joinpath("static")
        )
        damages_ra2ce_input.analysis_config.config_data.output_path = (
            _root_path.joinpath("output")
        )

        # Add adaptation analysis to the configuration
        _adaptation_config = AnalysisSectionAdaptation(
            analysis=AnalysisEnum.ADAPTATION,
            name="Adaptation",
            adaptation_options=[
                AnalysisSectionAdaptationOption(id="AO0"),
            ],
            save_csv=True,
            save_gpkg=True,
        )
        damages_ra2ce_input.analysis_config.config_data.analyses.append(
            _adaptation_config
        )

        # Copy input files for the adaptation analysis
        if _root_path.exists():
            rmtree(_root_path)
        damages_ra2ce_input.analysis_config.config_data.output_path.mkdir(parents=True)
        for _option in _adaptation_config.adaptation_options:
            _ao_path = (
                damages_ra2ce_input.analysis_config.config_data.input_path.joinpath(
                    _option.id
                )
            )
            copytree(test_data.joinpath("adaptation", "input"), _ao_path)
        copytree(
            test_data.joinpath("adaptation", "static"),
            damages_ra2ce_input.analysis_config.config_data.static_path,
        )

        # Read graph/network files
        damages_ra2ce_input.analysis_config.graph_files = (
            GraphFilesCollection.set_files(
                damages_ra2ce_input.analysis_config.config_data.static_path.joinpath(
                    "output_graph"
                ),
            )
        )

        _analysis_collection = AnalysisCollection(
            damages_analyses=None,
            losses_analyses=None,
            adaptation_analysis=AnalysisFactory.get_adaptation_analysis(
                damages_ra2ce_input.analysis_config.config_data.adaptation,
                damages_ra2ce_input.analysis_config,
            ),
        )

        # 2. Run test.
        _result = AdaptationAnalysisRunner().run(_analysis_collection)

        # 3. Verify expectation
        assert isinstance(_result, list)
        assert len(_result) == 1

        _result_wrapper = _result[0]
        assert isinstance(_result_wrapper, AnalysisResultWrapper)
        assert _result_wrapper.is_valid_result() == True

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
