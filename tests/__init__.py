"""Unit test package for ra2ce."""
import tempfile
from pathlib import Path

import pytest

slow_test = pytest.mark.slow_test
external_test = pytest.mark.external_test_data

_test_dir = Path(__file__).parent

test_data = _test_dir.joinpath("test_data")
acceptance_test_data = test_data.joinpath("acceptance_test_data")
test_external_data = _test_dir.joinpath("test_external_data")
test_examples = _test_dir.parent.joinpath("examples")

test_results = _test_dir.joinpath("test_results")
if not test_results.exists():
    test_results.mkdir()

temp_dir: Path = Path(tempfile.gettempdir())
