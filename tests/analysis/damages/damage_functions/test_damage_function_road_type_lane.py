import pytest

from ra2ce.analysis.damages.damage_functions.damage_function_road_type_lane import (
    DamageFunctionByRoadTypeByLane,
)
from tests import test_data


class TestDamageFunctionByRoadTypeByLane:
    def test_from_input_folder_without_damage_files_raises(self):
        # 1. Define test data.
        _damage_test_data = test_data / "damages" / "no_files"
        if not _damage_test_data.exists():
            _damage_test_data.mkdir(parents=True)

        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            DamageFunctionByRoadTypeByLane.from_input_folder(None, _damage_test_data)

        # 3. Verify final expectations.
        assert str(exc_err.value) == "Did not find any damage file in {}".format(
            _damage_test_data
        )

    def test_from_input_folder_with_too_many_files_raises(self):
        # 1. Define test data.
        _damage_test_data = test_data / "damages" / "repeated_files"
        # 2. Run test.
        with pytest.raises(ValueError) as exc_err:
            DamageFunctionByRoadTypeByLane.from_input_folder(None, _damage_test_data)

        # 3. Verify final expectations.
        assert str(exc_err.value) == "Found more then one damage file in {}".format(
            _damage_test_data
        )
