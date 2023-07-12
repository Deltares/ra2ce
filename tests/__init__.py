"""Unit test package for ra2ce."""
from pathlib import Path

import pytest

_test_dir = Path(__file__).parent

test_data = _test_dir / "test_data"
acceptance_test_data = test_data / "acceptance_test_data"
test_results = _test_dir / "test_results"
test_external_data = _test_dir / "test_external_data"

test_examples = _test_dir.parent.joinpath("examples")
slow_test = pytest.mark.slow_test
external_test = pytest.mark.skipif(
    not test_external_data.exists(), reason="No external test data available."
)
