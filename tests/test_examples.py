import subprocess
from pathlib import Path

import pytest

from tests import test_examples, test_results

_jupyter_examples = [
    pytest.param(
        _jupyter_notebook, id=_jupyter_notebook.stem.replace("_", " ").capitalize()
    )
    for _jupyter_notebook in test_examples.glob("*.ipynb")
]


class TestExamples:
    @pytest.mark.parametrize("jupyter_example", _jupyter_examples)
    @pytest.mark.skip(reason="Work in progress")
    def test_run_jupyter_from_examples_dir(
        self, jupyter_example: Path, request: pytest.FixtureRequest
    ):
        pass
