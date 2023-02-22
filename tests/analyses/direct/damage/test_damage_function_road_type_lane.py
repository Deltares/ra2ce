import pytest

from ra2ce.analyses.direct.damage.damage_function_road_type_lane import (
    DamageFunctionByRoadTypeByLane,
)
from tests import test_data


class TestDamageFunctionByRoadTypeByLane:
    def test_from_input_folder_without_damage_files_raises(self):
        # 1. Define test data.
        _damage_function = DamageFunctionByRoadTypeByLane()
        _damage_test_data = (
            test_data
            / "direct_damage"
            / "no_files"
        )
        if not _damage_test_data.exists():
            _damage_test_data.mkdir(parents=True)

        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            _damage_function.from_input_folder(_damage_test_data)

        # 3. Verify final expectations.
        assert str(exc_err.value) == "Did not find any damage file in {}".format(
            _damage_test_data
        )

    def test_from_input_folder_with_too_many_files_raises(self):
        # 1. Define test data.
        _damage_function = DamageFunctionByRoadTypeByLane()
        _damage_test_data = test_data / "direct_damage" / "repeated_files"
        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            _damage_function.from_input_folder(_damage_test_data)

        # 3. Verify final expectations.
        assert str(exc_err.value) == "Found more then one damage file in {}".format(
            _damage_test_data
        )
