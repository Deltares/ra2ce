from pathlib import Path
from typing import List

import pytest

from ra2ce.configuration.ini_config_protocol import IniConfigDataProtocol
from ra2ce.configuration.validators.ini_config_validator_base import (
    IniConfigValidatorBase,
)
from ra2ce.validation.validation_report import ValidationReport
from tests import test_data, test_results


class DummyConfigData(IniConfigDataProtocol):
    @classmethod
    def from_dict(cls, dict_values) -> IniConfigDataProtocol:
        _dummy_dict = cls()
        _dummy_dict.update(**dict_values)
        return _dummy_dict


class TestIniConfigValidatorBase:
    def test_initialize(self):
        _validator = IniConfigValidatorBase(DummyConfigData())
        assert _validator

    def test_validate_raises_not_implemented_error(self):
        """
        With this test we ensure NO VALIDATION is allowed in the base class `IniConfigValidatorBase`.
        """
        with pytest.raises(NotImplementedError):
            IniConfigValidatorBase(DummyConfigData()).validate()

    def test_validate_files_no_path_value_list_returns_empty_report(self):
        # 1. Define test data.
        _validator = IniConfigValidatorBase(DummyConfigData())

        # 2. Run test.
        _report = _validator._validate_files("does_not_matter", [])

        # 3. Verify expectations.
        assert isinstance(_report, ValidationReport)
        assert _report.is_valid()

    def test_validate_files_with_non_existing_files_reports_error(self):
        # 1. Define test data.
        _validator = IniConfigValidatorBase(DummyConfigData())
        _test_file = test_data / "not_a_valid_file.txt"

        # 2. Run test.
        _report = _validator._validate_files("dummy_header", [_test_file])

        # 3. Verify expectations.
        assert isinstance(_report, ValidationReport)
        assert not _report.is_valid()
        assert len(_report._errors) == 2

    def test_validate_road_types_no_road_type_returns_empty_report(self):
        # 1. Define test data.
        _validator = IniConfigValidatorBase(DummyConfigData())

        # 2. Run test.
        _report = _validator._validate_road_types("")

        # 3. Verify expectations.
        assert isinstance(_report, ValidationReport)
        assert _report.is_valid()

    def test_validate_road_types_with_unexpected_road_type_reports_error(self):
        # 1. Define test data.
        _validator = IniConfigValidatorBase(DummyConfigData())
        _road_type = "not a valid road type"

        # 2. Run test.
        _report = _validator._validate_road_types(_road_type)

        # 3. Verify expectations.
        assert isinstance(_report, ValidationReport)
        assert not _report.is_valid()
        assert len(_report._errors) == 1

    def _validate_headers_from_dict(
        self, dict_values: dict, required_headers: List[str]
    ) -> ValidationReport:
        _test_config_data = DummyConfigData.from_dict(dict_values)
        _validator = IniConfigValidatorBase(_test_config_data)
        return _validator._validate_headers(required_headers)

    def test_validate_headers_fails_when_missing_expected_header(self):
        # 1. Define test data.
        _test_config_data = {}
        _missing_header = "Deltares"
        _expected_err = f"Property [ {_missing_header} ] is not configured. Add property [ {_missing_header} ] to the *.ini file. "

        # 2. Run test.
        _report = self._validate_headers_from_dict(
            _test_config_data, required_headers=[_missing_header]
        )

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert _expected_err in _report._errors

    def test_validate_headers_fails_when_wrong_file_value(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        _required_header = "file_header"
        _test_config_data = {
            "root_path": test_results,
            "project": {"name": request.node.name},
            _required_header: {"polygon": [Path("sth")]},
        }

        # 2. Run test.
        _report = self._validate_headers_from_dict(
            _test_config_data, required_headers=[_required_header]
        )

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert len(_report._errors) == 3

    def test_validate_headers_fails_when_wrong_road_type(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        _required_header = "road_header"
        _test_config_data = {
            "root_path": test_results,
            "project": {"name": request.node.name},
            _required_header: {"road_types": "not a valid road type"},
        }

        # 2. Run test.
        _report = self._validate_headers_from_dict(
            _test_config_data, required_headers=[_required_header]
        )

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert len(_report._errors) == 2

    def test_validate_headers_fails_when_unexpected_value(
        self, request: pytest.FixtureRequest
    ):
        # 1. Define test data.
        _required_header = "unexpected_value"
        _test_config_data = {
            "root_path": test_results,
            "project": {"name": request.node.name},
            _required_header: {"network_type": "unmapped_value"},
        }

        # 2. Run test.
        _report = self._validate_headers_from_dict(
            _test_config_data, required_headers=[_required_header]
        )

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert len(_report._errors) == 2
