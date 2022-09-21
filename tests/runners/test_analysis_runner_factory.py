from pathlib import Path
from typing import Optional

import pytest

from ra2ce.runners.analysis_runner_factory import AnalysisRunnerFactory
from tests.runners.dummy_classes import DummyRa2ceInput


class TestAnalysisRunnerFactory:
    def test_get_runner_unknown_input_raises_error(self):
        with pytest.raises(ValueError) as exc_err:
            AnalysisRunnerFactory.get_runner(DummyRa2ceInput())

        assert (
            str(exc_err.value)
            == "No analysis runner found for the given configuration."
        )
