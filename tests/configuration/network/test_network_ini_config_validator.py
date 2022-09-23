from ra2ce.configuration.network.network_ini_config_data import NetworkIniConfigData
from ra2ce.configuration.network.network_ini_config_validator import (
    NetworkIniConfigurationValidator,
)
from ra2ce.validation.validation_report import ValidationReport


class TestNetworkIniConfigurationValidator:
    def _validate_from_dict(self, dict_values: dict) -> ValidationReport:
        _test_config_data = NetworkIniConfigData.from_dict(dict_values)
        _validator = NetworkIniConfigurationValidator(_test_config_data)
        return _validator.validate()

    def test_init_validator(self):
        _test_config_data = NetworkIniConfigData()
        _validator = NetworkIniConfigurationValidator(_test_config_data)
        assert _validator

    def test_validate_given_valid_config_data(self):
        # 1. Define test data.
        _test_config_data = {
            "project": dict(),
            "network": dict(source="pickle"),
            "origins_destinations": dict(),
            "hazard": dict(),
            "cleanup": dict(),
        }

        # 2. Run test.
        _report = self._validate_from_dict(_test_config_data)

        # 3. Verify final expectations.
        assert _report.is_valid()
        assert not _report._errors

    def test_validate_given_no_network_reports_fails(self):
        # 1. Define test data.
        _expected_err = "Network properties not present in Network ini file."
        _test_config_data = {"network": None}

        # 2. Run test.
        _report = self._validate_from_dict(_test_config_data)

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert _expected_err in _report._errors

    def test_validate_missing_shp_input_errors(self):
        # 1. Define test data.
        _expected_err = "Not possible to create network - Shapefile used as source, but no file_id configured in the network.ini file"
        _test_config_data = {"network": dict(source="shapefile", file_id=None)}

        # 2. Run test.
        _report = self._validate_from_dict(_test_config_data)

        # 3. Verify final expectations.
        assert not _report.is_valid()
        assert _expected_err in _report._errors
