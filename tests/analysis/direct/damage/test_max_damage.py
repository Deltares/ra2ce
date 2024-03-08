from ra2ce.analyses.direct.damage.max_damage import MaxDamageByRoadTypeByLane


class TestMaxDamageByRoadTypeByLane:
    def test_init(self):
        # 1. Define test data.
        _name = "sth"
        _dmg_unit = "else"

        # 2. Run test.
        _damage = MaxDamageByRoadTypeByLane(_name, _dmg_unit)

        # 3. Verify final expectations.
        assert isinstance(_damage, MaxDamageByRoadTypeByLane)
        assert _damage.name == _name
        assert _damage.damage_unit == _dmg_unit

    def test_convert_length_unit_same_unit_does_nothing(self):
        # 1. Define test data.
        _name = "sth"
        _dmg_unit = "else"
        _damage = MaxDamageByRoadTypeByLane(_name, _dmg_unit)

        # 2. Run test.
        _damage.convert_length_unit(_dmg_unit)

        # 3. Verify expectations
        assert _damage.damage_unit == _dmg_unit

    def test_convert_length_unit_unsupported_does_nothing(self):
        # 1. Define test data.
        _name = "my_damage"
        _dmg_unit = "sth/km"
        _desired_unit = "else/miles"
        _damage = MaxDamageByRoadTypeByLane(_name, _dmg_unit)
        _damage.data = 42.0

        # 2. Run test.
        _damage.convert_length_unit(_desired_unit)

        # 3. Verify expectations
        assert _damage.damage_unit == _dmg_unit
        assert _damage.data == 42.0
