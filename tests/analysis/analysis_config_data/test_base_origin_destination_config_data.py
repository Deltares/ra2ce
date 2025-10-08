import math
from dataclasses import is_dataclass
from os import link

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.base_origin_destination_config_data import (
    BaseOriginDestinationConfigData,
    MultiLinkOriginClosestDestinationConfigData,
    MultiLinkOriginDestinationConfigData,
    OptimalRouteOriginClosestDestinationConfigData,
    OptimalRouteOriginDestinationConfigData,
)
from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum


@pytest.mark.parametrize(
    "origin_destination_config_data_type", [
        OptimalRouteOriginDestinationConfigData,
        OptimalRouteOriginClosestDestinationConfigData,
        MultiLinkOriginDestinationConfigData,
        MultiLinkOriginClosestDestinationConfigData]
)
class TestOriginDestinationConfigData:
    def test_initialization(self, origin_destination_config_data_type: type[BaseOriginDestinationConfigData]) -> None:
        # 1. Define test data.
        _data_name = "Test Analysis"

        # 2. Run test.
        _origin_destination_config_data = origin_destination_config_data_type(
            name="Test Analysis")
        
        # 3. Verify expectations.
        assert isinstance(_origin_destination_config_data, origin_destination_config_data_type)
        assert isinstance(_origin_destination_config_data, BaseOriginDestinationConfigData)
        assert isinstance(_origin_destination_config_data, AnalysisConfigDataProtocol)
        assert is_dataclass(_origin_destination_config_data)
        assert _origin_destination_config_data.name == _data_name
        assert _origin_destination_config_data.save_gpkg is False
        assert _origin_destination_config_data.save_csv is False
        assert _origin_destination_config_data.weighing == WeighingEnum.NONE
        assert _origin_destination_config_data.calculate_route_without_disruption is False
        assert _origin_destination_config_data.threshold == 0.0
        assert math.isnan(_origin_destination_config_data.threshold_destinations)
        assert math.isnan(_origin_destination_config_data.buffer_meters)