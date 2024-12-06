import pytest
from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation import Adaptation
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from tests.analysis.adaptation.conftest import AdaptationOptionCases


class TestAdaptation:
    def test_initialize(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
    ):
        # 1./2. Define test data./Run test.
        _adaptation = Adaptation(valid_adaptation_config[0], valid_adaptation_config[1])

        # 3. Verify expectations.
        assert isinstance(_adaptation, Adaptation)

    def test_run_cost_returns_gdf(
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
            f"{_option.id}_cost" in _cost_gdf.columns
            for _option in _adaptation.adaptation_collection.adaptation_options
        )
        for _option, _, _total_cost in AdaptationOptionCases.cases[1:]:
            assert _cost_gdf[f"{_option.id}_cost"].sum(axis=0) == pytest.approx(
                _total_cost
            )

    def test_run_benefit_returns_gdf(
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
        
    def test_run_net_present_impact(
        self,
        valid_adaptation_input: AnalysisInputWrapper,
        valid_adaptation_config: AnalysisConfigData,
    ):
        # 1. Define test data.
        _adaptation = Adaptation(valid_adaptation_input, valid_adaptation_config)
        _adaptation.adaptation_collection.initial_frequency = 0.01
        _adaptation.adaptation_collection.climate_factor = 0.00036842
        _adaptation.adaptation_collection.discount_rate = 0.025
        _adaptation.adaptation_collection.time_horizon = 20

        # 2. Run test.
        _impact_gdf = _adaptation.run_net_present_impact()

        # 3. Verify expectations.
        assert isinstance(_impact_gdf, GeoDataFrame)
        assert all(
            [
                f"net_present_impact_{_option.id}" in _impact_gdf.columns
                for _option in _adaptation.adaptation_collection.adaptation_options
            ]
        )

