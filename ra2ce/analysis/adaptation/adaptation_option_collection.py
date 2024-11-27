from __future__ import annotations

from dataclasses import dataclass

from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData


@dataclass
class AdaptationOptionCollection:
    @classmethod
    def from_config(
        cls,
        analysis_config_data: AnalysisConfigData,
    ) -> AdaptationOptionCollection:
        return cls()
