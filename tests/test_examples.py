from pathlib import Path

import pytest
from tests import test_examples
from pytest_notebook.nb_regression import NBRegressionFixture, NBRegressionError
from pytest_notebook.notebook import NBConfigValidationError

_jupyter_examples = [
    pytest.param(
        _jupyter_notebook, id=_jupyter_notebook.stem.replace("_", " ").capitalize()
    )
    for _jupyter_notebook in test_examples.glob("*.ipynb")
]


class TestExamples:
    @pytest.mark.parametrize("jupyter_example", _jupyter_examples)
    @pytest.mark.documentation
    def test_run_jupyter_from_examples_dir(self, jupyter_example: Path):
        """
        https://pytest-notebook.readthedocs.io/en/latest/user_guide/tutorial_intro.html
        """
        try:
            _fixture = NBRegressionFixture(
                exec_notebook=True,
                exec_allow_errors=False,
                diff_color_words=False,
                exec_timeout=50,
                cov_config=None,
                cov_merge=None,
                cov_source=None,
            )
            _fixture.check(str(jupyter_example), raise_errors=True)
        except NBRegressionError:
            # We only verify whether the execution was succesful.
            # We DO NOT compare the execution to the previous generated results.
            pass
        except NBConfigValidationError:
            # These are the sort errors we are looking for :)
            raise
