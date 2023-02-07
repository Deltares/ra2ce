from typing import List

import pytest

from ra2ce.configuration.ini_config_protocol import IniConfigDataProtocol
from ra2ce.configuration.validators.ini_config_validator_base import (
    IniConfigValidatorBase,
)
from ra2ce.validation.validation_report import ValidationReport


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
