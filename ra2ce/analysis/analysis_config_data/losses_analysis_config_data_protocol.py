from typing import Protocol

from ra2ce.analysis.analysis_config_data.analysis_config_data_protocol import (
    AnalysisConfigDataProtocol,
)


class LossesAnalysisConfigDataProtocol(AnalysisConfigDataProtocol, Protocol):
    """Protocol for losses analysis configuration data."""
    pass