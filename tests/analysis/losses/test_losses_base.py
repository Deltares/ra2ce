import pytest

from ra2ce.analysis.losses.losses_base import LossesBase


class TestLossesBase:
    def test_initialize_base_class_raises(self):
        # 1. Run test.
        with pytest.raises(TypeError) as exc:
            LossesBase(None, None)

        # 2. Verify final expectations
        assert str(exc.value).startswith(
            f"Can't instantiate abstract class {LossesBase.__name__}"
        )
