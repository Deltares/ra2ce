from ra2ce.configuration.analysis.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.configuration.analysis.readers.analysis_without_network_config_reader import (
    AnalysisWithoutNetworkConfigReader,
    NetworkInAnalysisIniConfigReader,
)
from ra2ce.configuration.readers.ini_config_reader_base import (
    IniConfigurationReaderBase,
)


class TestNetworkInAnalysisIniConfigReader:
    def test_initialize(self):
        # 1. Run test.
        _reader = NetworkInAnalysisIniConfigReader()

        # 2. Verify expectations.
        assert isinstance(_reader, NetworkInAnalysisIniConfigReader)
        assert isinstance(_reader, IniConfigurationReaderBase)

    def test_read_without_ini_file_returns_none(self):
        # 1. Define test data.
        _reader = NetworkInAnalysisIniConfigReader()

        # 2. Run test
        _result = _reader.read(None)

        # 3. Verify expectations
        assert _result is None


class TestAnalysisWithoutNetworkConfigReader:
    def test_initialize(self):
        # 1. Run test.
        _reader = AnalysisWithoutNetworkConfigReader()

        # 2. Verify expectations.
        assert isinstance(_reader, AnalysisWithoutNetworkConfigReader)
        assert isinstance(_reader, AnalysisConfigReaderBase)

    def test_read_without_ini_file_returns_none(self):
        # 1. Define test data.
        _reader = AnalysisWithoutNetworkConfigReader()

        # 2. Run test
        _result = _reader.read(None)

        # 3. Verify expectations
        assert _result is None
