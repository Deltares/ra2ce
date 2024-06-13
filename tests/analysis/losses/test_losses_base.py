import pytest
from geopandas import GeoDataFrame

from ra2ce.analysis.analysis_config_wrapper import AnalysisConfigWrapper
from ra2ce.analysis.analysis_input_wrapper import AnalysisInputWrapper
from ra2ce.analysis.losses.analysis_losses_protocol import AnalysisLossesProtocol
from ra2ce.analysis.losses.losses_base import LossesBase


class MockLossesSubClass(LossesBase):
    analysis_input: AnalysisInputWrapper = None
    analysis: AnalysisLossesProtocol = None

    def __init__(
        self, analysis_input: AnalysisInputWrapper, config: AnalysisConfigWrapper
    ):
        self.analysis_input = analysis_input
        self.config = config

    def _get_criticality_analysis(self) -> AnalysisLossesProtocol:
        return MockRedundancyAnalysis(self.analysis_input)


class MockRedundancyAnalysis(AnalysisLossesProtocol):
    analysis_input: AnalysisInputWrapper = None

    def __init__(self, analysis_input: AnalysisInputWrapper):
        self.analysis_input = analysis_input

    def execute(self) -> GeoDataFrame | None:
        return GeoDataFrame()


class TestLossesBase:
    def test_initialize_base_class_raises(self):
        # 1. Run test.
        with pytest.raises(TypeError) as exc:
            _losses = LossesBase(None, None)

        # 2. Verify final expectations
        assert str(exc.value).startswith(
            f"Can't instantiate abstract class {LossesBase.__name__}"
        )

    def test_initialize_and_execute_subclass_doesnt_raise(self):
        # 1. Run test.
        _losses = MockLossesSubClass(None, None)
        _result = _losses.execute()

        # 2. Verify final expectations
        assert isinstance(_losses, LossesBase)
        assert _result.empty
