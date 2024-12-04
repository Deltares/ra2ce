from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation import Adaptation
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper


class TestAdaptation:
    def test_initialize(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
    ):
        # 1./2. Define test data./Run test.
        _adaptation = Adaptation(valid_adaptation_config[0], valid_adaptation_config[1])

        # 3. Verify expectations.
        assert isinstance(_adaptation, Adaptation)

    def test_run_cost(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
    ):
        # 1. Define test data.
        _adaptation = Adaptation(valid_adaptation_config[0], valid_adaptation_config[1])

        # 2. Run test.
        _cost_gdf = _adaptation.run_cost()

        # 3. Verify expectations.
        assert isinstance(_cost_gdf, GeoDataFrame)
        assert all(
            [
                f"{_option.id}_cost" in _cost_gdf.columns
                for _option in _adaptation.adaptation_collection.adaptation_options
            ]
        )

    def test_run_benefit(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
    ):
        # 1. Define test data.
        _adaptation = Adaptation(valid_adaptation_config[0], valid_adaptation_config[1])

        # 2. Run test.
        _result = _adaptation.run_benefit()

        # 3. Verify expectations.
        assert isinstance(_result, GeoDataFrame)
        assert all(
            [
                f"{_option.id}_impact" in _result.columns
                for _option in _adaptation.adaptation_collection.all_options
            ]
        )
