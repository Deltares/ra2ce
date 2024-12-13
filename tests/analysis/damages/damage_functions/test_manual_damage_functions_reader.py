from ra2ce.analysis.damages.damage_functions.manual_damage_functions import (
    ManualDamageFunctions,
)
from ra2ce.analysis.damages.damage_functions.manual_damage_functions_reader import (
    ManualDamageFunctionsReader,
)
from ra2ce.common.io.readers.file_reader_protocol import FileReaderProtocol
from tests import test_data


class TestManualDamageFunctionsReader:
    def test_initialize(self):
        # 1. Run test
        _reader = ManualDamageFunctionsReader()

        # 2. Verify expections
        assert isinstance(_reader, ManualDamageFunctionsReader)
        assert isinstance(_reader, FileReaderProtocol)

    def test_read_returns_manual_damage_functions(self):
        # 1. Define test data
        _path = test_data.joinpath("damages", "test_damage_functions")
        assert _path.exists()

        # 2. Execute test
        _result = ManualDamageFunctionsReader().read(_path)

        # 3. Verify expectations
        assert isinstance(_result, ManualDamageFunctions)
        assert len(_result.damage_functions) == 1
