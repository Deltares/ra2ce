from ra2ce.analysis.damages.damage_functions.max_damage import MaxDamage


class TestMaxDamage:
    def test_initialize(self):
        # 1. Define test data.
        _name = "sth"
        _dmg_unit = "else/m"

        # 2. Run test.
        _damage = MaxDamage(name=_name, damage_unit=_dmg_unit, data=42.0)

        # 3. Verify final expectations.
        assert isinstance(_damage, MaxDamage)
        assert _damage.name == _name
        assert _damage.damage_unit == _dmg_unit

    # Mock to avoid execution of __post_init__ method
    class MockMaxDamage(MaxDamage):
        def __post_init__(self) -> None:
            pass

    def test__convert_length_unit_converts_to_m(self):
        # 1. Define test data.
        _name = "sth"
        _dmg_unit = "else/km"
        _desired_unit = "else/m"
        _data = 42.0
        _damage = self.MockMaxDamage(name=_name, damage_unit=_dmg_unit, data=_data)

        # 2. Run test.
        _damage._convert_length_unit(_desired_unit)

        # 3. Verify expectations
        assert _damage.damage_unit == _desired_unit
        assert _damage.data == _data / 1000

    def test__convert_length_unit_same_unit_does_nothing(self):
        # 1. Define test data.
        _name = "sth"
        _dmg_unit = "else"
        _damage = self.MockMaxDamage(name=_name, damage_unit=_dmg_unit, data=None)

        # 2. Run test.
        _damage._convert_length_unit(_dmg_unit)

        # 3. Verify expectations
        assert _damage.damage_unit == _dmg_unit

    def test__convert_length_unit_unsupported_does_nothing(self):
        # 1. Define test data.
        _name = "my_damage"
        _dmg_unit = "sth/km"
        _desired_unit = "else/miles"
        _damage = self.MockMaxDamage(name=_name, damage_unit=_dmg_unit, data=42.0)

        # 2. Run test.
        _damage._convert_length_unit(_desired_unit)

        # 3. Verify expectations
        assert _damage.damage_unit == _dmg_unit
        assert _damage.data == 42.0
