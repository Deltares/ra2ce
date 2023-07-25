import pytest

from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_base import (
    AnalysisConfigWrapperBase,
)


class TestAnalysisConfigWrapperBase:
    def test_initialize(self):
        with pytest.raises(TypeError) as exc_error:
            AnalysisConfigWrapperBase()
        assert "Can't instantiate abstract class" in str(exc_error.value)
