from pathlib import Path

from ra2ce.analysis.adaptation.adaptation_option_collection import (
    AdaptationOptionCollection,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import (
    AnalysisConfigDataReader,
)


class TestAdaptationOptionCollection:
    def test_initialize(self):
        # 1./2. Define test data./Run test.
        _collection = AdaptationOptionCollection()

        # 3. Verify expectations.
        assert isinstance(_collection, AdaptationOptionCollection)

    def test_from_config(self, valid_analysis_ini: Path):
        # 1.Define test data.
        _config_data = AnalysisConfigDataReader().read(valid_analysis_ini)

        # 2. Run test.
        _collection = AdaptationOptionCollection.from_config(_config_data)

        # 3. Verify expectations.
        assert isinstance(_collection, AdaptationOptionCollection)
