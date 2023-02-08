from ra2ce.io.readers.ini_file_reader import IniFileReader
from tests.io.readers import test_data_readers


class TestIniFileReader:
    def test_given_valid_ini_file_reads_to_dict(self):
        # 1. Define test data.
        _ini_file = test_data_readers / "dummy.ini"
        assert _ini_file.is_file()

        _expected_dict = dict(
            project=dict(name="DummyIniFile"),
            analysis1=dict(
                name="justAnAnalysis",
                analysis="of any type",
                bool_value=True,
                int_value=42,
                float_value=4.2,
            ),
        )

        # 2. Run test.
        ini_data = IniFileReader().read(_ini_file)

        # 3. Verify final expectations.
        assert ini_data
        assert type(ini_data) == dict
        assert ini_data == _expected_dict
