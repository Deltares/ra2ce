import pytest

from ra2ce.configuration.analysis.readers.analysis_with_network_config_reader import (
    AnalysisWithNetworkConfigReader,
)


class TestAnalysisWithNetworkConfigReader:
    def test_init_without_network_data_raises(self):
        # 1. Run test.
        with pytest.raises(ValueError) as exc_err:
            AnalysisWithNetworkConfigReader(None)

        # 2. Verify expectations.
        assert (
            str(exc_err.value)
            == "Network data mandatory for an AnalysisIniConfigurationReader reader."
        )

    def test_read_without_ini_file_returns_none(self):
        # 1. Define test data.
        _reader = AnalysisWithNetworkConfigReader("sth")

        # 2. Run test
        _result = _reader.read(None)

        # 3. Verify expectations.
        assert _result is None
