from tests import test_examples
from pathlib import Path
import pytest

_jupyter_examples = [
    pytest.param(_jupyter_notebook, id=_jupyter_notebook.replace("_", " ").capitalize())
    for _jupyter_notebook in test_examples.glob("*.ipynb")
]


class TestExamples:
    @pytest.mark.parametrize("jupyter_example", _jupyter_examples)
    def test_run_jupyter_from_examples_dir(self, jupyter_example: Path):
        pytest.fail("Work in progress: {}".format(jupyter_example.name))
