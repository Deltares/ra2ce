"""Unit test package for ra2ce."""
from pathlib import Path

import pytest

_test_dir = Path(__file__).parent

test_data = _test_dir / "test_data"
acceptance_test_data = test_data / "acceptance_test_data"
test_results = _test_dir / "test_results"

slow_test = pytest.mark.slow_test
