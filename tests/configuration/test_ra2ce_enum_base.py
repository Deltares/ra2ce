import pytest

from ra2ce.configuration.ra2ce_enum_base import Ra2ceEnumBase


class MockEnum(Ra2ceEnumBase):
    NONE = 0
    FIRST = 1
    SECOND_ITEM = 2
    INVALID = 99


class MockEnumWithoutNone(Ra2ceEnumBase):
    FIRST = 1
    SECOND_ITEM = 2
    INVALID = 99


class TestRa2ceEnumBase:
    def test_get_enum_base_raises(self):
        # 1./2. Define test data / Run test
        with pytest.raises(AttributeError) as exc_err:
            Ra2ceEnumBase.get_enum("sth")

        # 3. Verify results
        # Disclaimer: Done like this as in Python 3.11 the exception error differs slightly.
        assert "INVALID" in str(exc_err.value)

    @pytest.mark.parametrize(
        "config_name, expected_outcome",
        [
            pytest.param("first", MockEnum.FIRST, id="simple"),
            pytest.param("second_item", MockEnum.SECOND_ITEM, id="with underscore"),
            pytest.param(None, MockEnum.NONE, id="None"),
            pytest.param("unknown", MockEnum.INVALID, id="invalid"),
        ],
    )
    def test_get_enum(self, config_name: str, expected_outcome: Ra2ceEnumBase):
        # 1./2. Define test data / Run test
        _enum = MockEnum.get_enum(config_name)

        # 3. Verify results
        assert _enum == expected_outcome

    def test_get_enum_without_none(self):
        # 1./2. Define test data / Run test
        _enum = MockEnumWithoutNone.get_enum(None)

        # 3. Verify results
        assert _enum == MockEnumWithoutNone.INVALID

    def test_get_config_name_base_raises(self):
        # 1./2. Define test data / Run test
        with pytest.raises(AttributeError) as exc_err:
            Ra2ceEnumBase.INVALID.config_value

        # 3. Verify results
        # Disclaimer: Done like this as in Python 3.11 the exception error differs slightly.
        assert "INVALID" in str(exc_err.value)

    @pytest.mark.parametrize(
        "enum, expected_value",
        [
            pytest.param(MockEnum.FIRST, "first", id="simple"),
            pytest.param(MockEnum.SECOND_ITEM, "second_item", id="with underscore"),
            pytest.param(MockEnum.NONE, None, id="None"),
            pytest.param(MockEnum.INVALID, "invalid", id="invalid"),
        ],
    )
    def test_get_config_value(self, enum: Ra2ceEnumBase, expected_value: str):
        # 1./2. Define test data / Run test
        _value = enum.config_value

        # 3. Verify results
        assert _value == expected_value

    @pytest.mark.parametrize(
        "enum, expected_value",
        [
            pytest.param(MockEnum.FIRST, True, id="simple"),
            pytest.param(MockEnum.SECOND_ITEM, True, id="with underscore"),
            pytest.param(MockEnum.NONE, True, id="None"),
            pytest.param(MockEnum.INVALID, False, id="invalid"),
        ],
    )
    def test_is_valid(self, enum: Ra2ceEnumBase, expected_value: bool):
        # 1./2. Define test data / Run test
        _valid = enum.is_valid()

        # 3. Verify results
        assert _valid == expected_value

    def test_list_valid_options(self):
        # 1./2. Define test data / Run test
        _options = MockEnum.list_valid_options()

        # 3. Verify results
        assert all(
            _option in _options
            for _option in [MockEnum.NONE, MockEnum.FIRST, MockEnum.SECOND_ITEM]
        )

    def test_list_valid_options_without_none(self):
        # 1./2. Define test data / Run test
        _options = MockEnumWithoutNone.list_valid_options()

        # 3. Verify results
        all(_option in _options for _option in [MockEnum.FIRST, MockEnum.SECOND_ITEM])
