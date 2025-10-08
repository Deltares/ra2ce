from pathlib import Path
from typing import Any

import pytest

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)
from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import (
    AnalysisConfigDataReader,
)
from ra2ce.analysis.analysis_config_data.base_link_losses_config_data import (
    MultiLinkLossesConfigData,
    SingleLinkLossesConfigData,
)
from ra2ce.analysis.analysis_config_data.base_origin_destination_config_data import (
    MultiLinkOriginClosestDestinationConfigData,
    MultiLinkOriginDestinationConfigData,
    OptimalRouteOriginClosestDestinationConfigData,
    OptimalRouteOriginDestinationConfigData,
)
from ra2ce.analysis.analysis_config_data.damages_config_data import DamagesConfigData
from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import (
    AnalysisDamagesEnum,
)
from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import (
    AnalysisLossesEnum,
)
from ra2ce.analysis.analysis_config_data.multi_link_redundancy_config_data import (
    MultiLinkRedundancyConfigData,
)
from ra2ce.analysis.analysis_config_data.single_link_redundancy_config_data import (
    SingleLinkRedundancyConfigData,
)
from tests import acceptance_test_data


class TestAnalysisConfigDataReader:
    def test_initialize(self):
        # 1. Run test.
        _reader = AnalysisConfigDataReader()

        # 2. Verify expectations.
        assert isinstance(_reader, AnalysisConfigDataReader)

    @pytest.mark.parametrize(
        "ini_file",
        [
            pytest.param(None, id="None"),
            pytest.param("", id="Str"),
            pytest.param(Path("InvalidPath"), id="Non existent path."),
            pytest.param(Path("InvalidPath.ini"), id="Non existent path file."),
        ],
    )
    def test_read_without_ini_file_raises_error(self, ini_file: Any):
        # 1. Run test.
        with pytest.raises(ValueError) as exc_err:
            AnalysisConfigDataReader().read(ini_file)

        # 2. Verify expectations.
        assert str(exc_err.value) == "No analysis ini file 'Path' provided."

    def test_read_succeeds(self):
        # 1. Define test data
        _ini_file = acceptance_test_data.joinpath("analyses.ini")

        # 2. Run test
        _config = AnalysisConfigDataReader().read(_ini_file)

        # 3. Verify expectations
        assert isinstance(_config.input_path, Path)

    @pytest.mark.parametrize(
        "analysis_config_name, expected_analysis_type",
        [
            pytest.param(
                AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY.config_value,
                SingleLinkRedundancyConfigData,
                id="Single link redundancy",
            ),
            pytest.param(
                AnalysisLossesEnum.MULTI_LINK_REDUNDANCY.config_value,
                MultiLinkRedundancyConfigData,
                id="Multi link redundancy",
            ),
            pytest.param(
                AnalysisLossesEnum.SINGLE_LINK_LOSSES.config_value,
                SingleLinkLossesConfigData,
                id="Single link losses",
            ),
            pytest.param(
                AnalysisLossesEnum.MULTI_LINK_LOSSES.config_value,
                MultiLinkLossesConfigData,
                id="Multi link losses",
            ),
            pytest.param(
                AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_DESTINATION.config_value,
                OptimalRouteOriginDestinationConfigData,
                id="Optimal route origin destination",
            ),
            pytest.param(
                AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_CLOSEST_DESTINATION.config_value,
                OptimalRouteOriginClosestDestinationConfigData,
                id="Optimal route origin closest destination",
            ),
            pytest.param(
                AnalysisLossesEnum.MULTI_LINK_ORIGIN_DESTINATION.config_value,
                MultiLinkOriginDestinationConfigData,
                id="Multi link origin destination",
            ),
            pytest.param(
                AnalysisLossesEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION.config_value,
                MultiLinkOriginClosestDestinationConfigData,
                id="Multi link origin closest destination"
            ),
            pytest.param(
                AnalysisDamagesEnum.DAMAGES.config_value,
                DamagesConfigData,
                id="Damages",
            ),
        ],
    )
    def test_get_analysis_sections_with_new_dataclasses(
        self,
        analysis_config_name: str,
        expected_analysis_type: type[AnalysisConfigDataProtocol],
    ):
        """
        Integration test targeting multiple 'private' methods and properties.
        It ensures that the correct dataclass is being mapped to the correct analysis type.
        It does so by injecting test data in the parser, instead of creating multiple files.
        """
        # 1. Define test data
        _reader = AnalysisConfigDataReader()
        _section_name = "dummy_analysis"
        _analysis_name = analysis_config_name + " test"
        _reader._parser.add_section(_section_name)
        _reader._parser.set(_section_name, "name", _analysis_name)
        _reader._parser.set(_section_name, "analysis", analysis_config_name)
        _reader._parser.set(_section_name, "save_csv", "True")
        _reader._parser.set(_section_name, "save_gpkg", "True")

        # 2. Run test

        # Read everything so it gets correctly initialized.
        _analyses_config_data = _reader._get_analysis_sections_with_new_dataclasses()

        # 3. Verify expectations
        assert isinstance(_analyses_config_data, list)
        assert len(_analyses_config_data) == 1
        _first_slr_cd = _analyses_config_data[0]
        assert isinstance(_first_slr_cd, expected_analysis_type)
        assert _first_slr_cd.name == _analysis_name
        assert _first_slr_cd.save_csv is True
        assert _first_slr_cd.save_gpkg is True
