import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
from ra2ce.analysis.analysis_config_data.single_link_redundancy_config_data import (
    SingleLinkRedundancyConfigData,
)


class TestSingleLinkRedundancyConfigData:
    
    def test_initialize_with_required_values(self):
        # 1. Define test data.
        _name = "TestConfig"

        # 2. Run test.
        config = SingleLinkRedundancyConfigData(name=_name)

        # 3. Verify expectations.
        assert isinstance(config, SingleLinkRedundancyConfigData)
        assert isinstance(config, AnalysisConfigDataProtocol)
        assert config.name == _name
        assert config.save_gpkg is False
        assert config.save_csv is False
        assert config.weighing == WeighingEnum.NONE
    
    def test_initialize_without_required_values_fails(self):
        # 1. Define test data.
        _expected_error = "SingleLinkRedundancyConfigData.__init__() missing 1 required positional argument: 'name'"

        # 2. Run test and verify expectations.
        with pytest.raises(TypeError) as exc_info:
            _ = SingleLinkRedundancyConfigData()  # type: ignore

        # 3. Verify expectations.
        assert str(exc_info.value) == _expected_error