import pytest

from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.adaptation.adaptation_option_collection import (
    AdaptationOptionCollection,
)
from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper


class TestAdaptationOptionCollection:
    def test_initialize(self):
        # 1./2. Define test data./Run test.
        _collection = AdaptationOptionCollection()

        # 3. Verify expectations.
        assert isinstance(_collection, AdaptationOptionCollection)

    def test_from_config(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
    ):
        # 1./2. Define test data./Run test.
        _collection = AdaptationOptionCollection.from_config(valid_adaptation_config[1])

        # 3. Verify expectations.
        assert isinstance(_collection, AdaptationOptionCollection)

        assert isinstance(_collection.reference_option, AdaptationOption)
        assert _collection.reference_option.id == "AO0"

        assert len(_collection.all_options) == len(
            valid_adaptation_config[1].config_data.adaptation.adaptation_options
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

    def test_calculate_options_unit_cost(
        self,
        valid_adaptation_config: tuple[AnalysisInputWrapper, AnalysisConfigWrapper],
    ):
        # 1. Define test data.
        _collection = AdaptationOptionCollection.from_config(valid_adaptation_config[1])

        # 2. Run test.
        _result = _collection.calculate_options_unit_cost()

        # 3. Verify expectations.
        assert isinstance(_result, dict)
        assert all(_option in _result for _option in _collection.adaptation_options)
