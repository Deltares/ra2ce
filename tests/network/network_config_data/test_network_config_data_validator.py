from pathlib import Path

import pytest

from ra2ce.common.validation.validation_report import ValidationReport
from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
from ra2ce.network.network_config_data.network_config_data import (
    CleanupSection,
    HazardSection,
    NetworkConfigData,
    NetworkSection,
    OriginsDestinationsSection,
    ProjectSection,
)
from ra2ce.network.network_config_data.network_config_data_validator import (
    NetworkConfigDataValidator,
)


class TestNetworkConfigDataValidator:
    def test_init_validator(self):
        _test_config_data = NetworkConfigData()
        _validator = NetworkConfigDataValidator(_test_config_data)
        assert _validator

    def test_validate_given_valid_config_data(self):
        # 1. Define test data.
        _test_config_data = NetworkConfigData(
            root_path=Path("dummy_path"),
            static_path=Path("dummy_path"),
            **{
                "project": ProjectSection(name=""),
                "network": NetworkSection(source=SourceEnum.PICKLE),
                "origins_destinations": OriginsDestinationsSection(),
                "hazard": HazardSection(),
                "cleanup": CleanupSection(),
            },
        )

        # 2. Run test.
        _report = NetworkConfigDataValidator(_test_config_data).validate()

        # 3. Verify final expectations.
        assert isinstance(_report, ValidationReport)
        assert _report.is_valid()
        assert not _report._errors

    @pytest.mark.parametrize(
        "config_data",
        [
            pytest.param(
                NetworkConfigData(root_path=None, static_path=Path("dummy_path")),
                id="no_root_path",
            ),
            pytest.param(
                NetworkConfigData(root_path=Path("dummy_path"), static_path=None),
                id="no_static_path",
            ),
        ],
    )
    def test_validate_without_required_path_fails(self, config_data: NetworkConfigData):
        # 1. Define test data.
        _expected_err = "Root or static path not properly set."

        # 2. Run test.
        _report = NetworkConfigDataValidator(config_data).validate()

        # 3. Verify expectations.
        assert isinstance(_report, ValidationReport)
        assert not _report.is_valid()
        assert _expected_err in _report._errors

    def test_validate_given_no_network_reports_fails(self):
        # 1. Define test data.
        _expected_err = "Network properties not present in Network ini file."
        _test_config_data = NetworkConfigData(
            root_path=Path("dummy_path"),
            static_path=Path("dummy_path"),
            network=None,
        )

        # 2. Run test.
        _report = NetworkConfigDataValidator(_test_config_data).validate()

        # 3. Verify final expectations.
        assert isinstance(_report, ValidationReport)
        assert not _report.is_valid()
        assert _expected_err in _report._errors
