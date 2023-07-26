from ra2ce.analyses.analysis_config_data.readers.analysis_config_reader_base import (
    AnalysisConfigReaderBase,
)
from ra2ce.analyses.analysis_config_data.readers.analysis_without_network_config_reader import (
    AnalysisConfigReaderWithoutNetwork,
)


class TestAnalysisWithoutNetworkConfigReader:
    def test_initialize(self):
        # 1. Run test.
        _reader = AnalysisConfigReaderWithoutNetwork()

        # 2. Verify expectations.
        assert isinstance(_reader, AnalysisConfigReaderWithoutNetwork)
        assert isinstance(_reader, AnalysisConfigReaderBase)

    def test_read_without_ini_file_returns_none(self):
        # 1. Define test data.
        _reader = AnalysisConfigReaderWithoutNetwork()

        # 2. Run test
        _result = _reader.read(None)

        # 3. Verify expectations
        assert _result is None
