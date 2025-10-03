import re
from pathlib import Path

import pytest
from pytest_notebook.execution import execute_notebook
from pytest_notebook.notebook import load_notebook

from tests import test_examples
from tests.output_validator.output_validator import OutputValidator

_supported_examples = lambda x: "DIY" not in x.stem
_jupyter_examples = [
    pytest.param(_jupyter_file, id=_jupyter_file.stem.replace("_", " ").capitalize())
    for _jupyter_file in filter(_supported_examples, test_examples.glob("*.ipynb"))
]


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

        def _get_path(input_str: str) -> Path:
            # Strip of spaces, quotes and slashes, then split on commas and join again.
            _parts = [s.strip(' "\\') for s in input_str.split(",")]
            return Path().joinpath(*_parts)

        def _find_root_dirs() -> list[Path]:
            # Look for lines that set the root_dir variable.
            _jupyter_content = jupyter_example.read_text()
            _matches = re.findall(r"root_dir\s?=\s?Path\((.*?)\)", _jupyter_content)
            if _matches:
                return [_get_path(_match) for _match in _matches]
            return []

        # Validate the output(s) of the notebook against the reference output(s).
        for _root_dir in _find_root_dirs() or []:
            _example_dir = test_examples.joinpath(_root_dir)
            if not _example_dir or not _example_dir.joinpath("reference").is_dir():
                continue
            OutputValidator(_example_dir).validate_results()
