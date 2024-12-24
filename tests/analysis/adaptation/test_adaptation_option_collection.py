from dataclasses import dataclass

import pytest
from geopandas import GeoDataFrame

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.adaptation.adaptation_option_collection import (
    AdaptationOptionCollection,
)
from ra2ce.analysis.adaptation.adaptation_partial_result import AdaptationPartialResult
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper


class TestAdaptationOptionCollection:
    def test_initialize(self):
        # 1./2. Define test data./Run test.
        _collection = AdaptationOptionCollection()

        # 3. Verify expectations.
        assert isinstance(_collection, AdaptationOptionCollection)

    def test_from_config_returns_object(
        self,
        valid_adaptation_config: AnalysisConfigWrapper,
    ):
        # 1./2. Define test data./Run test.
        _collection = AdaptationOptionCollection.from_config(valid_adaptation_config)

        # 3. Verify expectations.
        assert isinstance(_collection, AdaptationOptionCollection)

        assert isinstance(_collection.reference_option, AdaptationOption)
        assert _collection.reference_option.id == "AO0"

        assert len(_collection.all_options) == len(
            valid_adaptation_config.config_data.adaptation.adaptation_options
        )

        assert all(
            isinstance(x, AdaptationOption) for x in _collection.adaptation_options
        )
        for i, _option in enumerate(_collection.adaptation_options):
            assert _option.id == f"AO{i+1}"

    def test_from_config_no_adaptation_raises(self):
        # 1. Define test data.
        _config = AnalysisConfigWrapper()

        # 2. Run test.
        with pytest.raises(ValueError) as _exc:
            AdaptationOptionCollection.from_config(_config)

        # 3. Verify expectations.
        assert _exc.match("No adaptation section found in the analysis config data.")

    def test_calculate_options_unit_cost_returns_dict(
        self,
        valid_adaptation_config: AnalysisConfigWrapper,
    ):
        # 1. Define test data.
        _collection = AdaptationOptionCollection.from_config(valid_adaptation_config)

        # 2. Run test.
        _result = _collection.calculate_options_unit_cost()

        # 3. Verify expectations.
        assert isinstance(_result, dict)
        assert all(_option in _result for _option in _collection.adaptation_options)

    def test_calculate_options_benefit_returns_result(self):
        @dataclass
        class MockOption(AdaptationOption):
            # Mock to avoid the need to run the impact analysis.
            impact: float = 0.0

            def calculate_impact(self, _) -> AdaptationPartialResult:
                _impact_gdf = GeoDataFrame.from_dict(
                    {_id_col: range(10), f"{self.id}_net_impact": self.impact}
                )
                return AdaptationPartialResult(_id_col, _impact_gdf)

        # 1. Define test data.
        _id_col = "link_id"
        _nof_rows = 10
        _reference_benefit = 5.0e6
        _options = {f"Option{i}": _reference_benefit - (i * 1.0e6) for i in range(3)}
        _collection = AdaptationOptionCollection(
            all_options=[
                MockOption(
                    id=x,
                    name=None,
                    construction_cost=None,
                    construction_interval=None,
                    maintenance_cost=None,
                    maintenance_interval=None,
                    analyses=None,
                    analysis_config=None,
                    impact=y,
                )
                for x, y in _options.items()
            ]
        )

        # 2. Run test.
        _result = _collection.calculate_options_benefit()

        # 3. Verify expectations.
        assert isinstance(_result, AdaptationPartialResult)
        assert all(
            f"{_option.id}_benefit" in _result.data_frame.columns
            for _option in _collection.adaptation_options
        )
        assert all(
            _result.data_frame[f"{_id}_benefit"].sum(axis=0)
            == pytest.approx(_nof_rows * (_reference_benefit - _impact))
            for _id, _impact in _options.items()
            if _id != "Option0"
        )

    def test_calculate_correct_get_net_present_value_factor(
        self,
        valid_adaptation_config: AnalysisConfigWrapper,
    ):
        # 1. Define test data.
        _collection = AdaptationOptionCollection.from_config(valid_adaptation_config)

        # 2. Run test.
        _result = _collection.get_net_present_value_factor()

        # 3. Verify expectations.
        assert isinstance(_result, float)
        assert _result == pytest.approx(0.2109011023, rel=1e-9)
