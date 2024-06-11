import math
from typing import Any

from ra2ce.analysis.losses.weighing_analysis.weighing_analysis_protocol import (
    WeighingAnalysisProtocol,
)


class LengthWeighingAnalysis(WeighingAnalysisProtocol):
    weighing_data: dict[str, Any]

    def __init__(self) -> None:
        pass

    def calculate_current_value(self) -> float:
        return math.nan

    def calculate_alternative_value(self, alt_dist: float) -> float:
        return alt_dist
