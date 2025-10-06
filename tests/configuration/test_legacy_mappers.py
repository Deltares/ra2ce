from dataclasses import dataclass

from ra2ce.configuration.legacy_mappers import with_legacy_mappers


class TestBaseLegacyIniMapper:
    def test_initialize_subclass_succeeds(self):
        # 1. Define test data.

        @with_legacy_mappers
        @dataclass
        class ConcreteLegacyIniMapper:
            name: str
            value: int = 0

        _data = {"name": "test", "value": 42, "analysis": "invalid"}

        # 2. Run test.
        _instance = ConcreteLegacyIniMapper.from_ini_file(**_data)

        # 3. Verify expectations.
        assert isinstance(_instance, ConcreteLegacyIniMapper)
        assert _instance.name == "test"
        assert _instance.value == 42
        assert "analysis" not in _instance.__dict__.keys()
