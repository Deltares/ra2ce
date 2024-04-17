from pytest_notebook.execution import execute_notebook
from pytest_notebook.notebook import load_notebook
from pathlib import Path

from tests import test_examples

_supported_examples = lambda x: "DIY" not in x.stem
_jupyter_examples = [
    pytest.param(_jupyter_file, id=_jupyter_file.stem.replace("_", " ").capitalize())
    for _jupyter_file in filter(_supported_examples, test_examples.glob("*.ipynb"))
]

import pytest


class TestExamples:
    @pytest.mark.parametrize("jupyter_example", _jupyter_examples)
    @pytest.mark.documentation
    def test_run_jupyter_from_examples_dir(self, jupyter_example: Path):
        """
        Apparently it hangs on the "passing tests" when using the approach of:
        https://pytest-notebook.readthedocs.io/en/latest/user_guide/tutorial_intro.html
        Therefore we just implement our own way of checking whether the examples run,
        without comparing the results.
        """
        _execution_result = execute_notebook(
            notebook=load_notebook(str(jupyter_example)),
            cwd=jupyter_example.parent,
            allow_errors=False,
            timeout=600,
        )

        if _execution_result.exec_error:
            # If execution errors were found then raise the exception so the
            # output looks "beautiful", instead of using `pytest.raises(...)`
            raise _execution_result.exec_error
