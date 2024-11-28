from ra2ce.analysis.adaptation.adaptation_option import AdaptationOption
from ra2ce.analysis.adaptation.adaptation_option_collection import (
    AdaptationOptionCollection,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)


class TestAdaptationOptionCollection:
    def test_initialize(self):
        # 1./2. Define test data./Run test.
        _collection = AdaptationOptionCollection()

        # 3. Verify expectations.
        assert isinstance(_collection, AdaptationOptionCollection)

    def test_from_config(self, valid_adaptation_config: AnalysisConfigData):
        # 1./2. Define test data./Run test.
        _collection = AdaptationOptionCollection.from_config(valid_adaptation_config)

        # 3. Verify expectations.
        assert isinstance(_collection, AdaptationOptionCollection)

        assert isinstance(_collection.no_adaptation_option, AdaptationOption)
        assert _collection.no_adaptation_option.id == "AO0"

        assert len(_collection.adaptation_options) == 2
        assert all(
            isinstance(x, AdaptationOption) for x in _collection.adaptation_options
        )
        for i, _option in enumerate(_collection.adaptation_options):
            assert _option.id == f"AO{i+1}"
