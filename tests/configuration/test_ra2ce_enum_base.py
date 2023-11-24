import pytest

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class MockEnum(Ra2ceEnumBase):
    FIRST = 1
    SECOND_ITEM = 2
    INVALID = 99


class TestRa2ceEnumBase:
    def test_get_enum_base_raises(self):
        # 1./2. Define test data / Run test
        with pytest.raises(AttributeError) as exc_err:
            _enum = Ra2ceEnumBase.get_enum("sth")

        # 3. Verify results
        assert str(exc_err.value) == "INVALID"

    @pytest.mark.parametrize(
        "config_name, expected_outcome",
        [
            pytest.param("first", MockEnum.FIRST, id="simple"),
            pytest.param("second_item", MockEnum.SECOND_ITEM, id="with underscore"),
            pytest.param("unknown", MockEnum.INVALID, id="invalid"),
        ],
    )
    def test_get_enum(self, config_name: str, expected_outcome: Ra2ceEnumBase):
        # 1./2. Define test data / Run test
        _enum = MockEnum.get_enum(config_name)

        # 3. Verify results
        assert _enum == expected_outcome

    def test_get_config_name_base_raises(self):
        # 1./2. Define test data / Run test
        with pytest.raises(AttributeError) as exc_err:
            _name = Ra2ceEnumBase.INVALID.config_value

        # 3. Verify results
        assert str(exc_err.value) == "INVALID"

    @pytest.mark.parametrize(
        "enum, expected_value",
        [
            pytest.param(MockEnum.FIRST, "first", id="simple"),
            pytest.param(MockEnum.SECOND_ITEM, "second_item", id="with underscore"),
        ],
    )
    def test_get_config_value(self, enum: Ra2ceEnumBase, expected_value: str):
        # 1./2. Define test data / Run test
        _value = enum.config_value

        # 3. Verify results
        assert _value == expected_value
