from typing import Protocol, runtime_checkable

from ra2ce.configuration import AnalysisConfigBase
from ra2ce.configuration.config_wrapper import ConfigWrapper


@runtime_checkable
class AnalysisRunner(Protocol):
    @staticmethod
    def can_run(ra2ce_input: ConfigWrapper) -> bool:
        """
        Validates whether the given `ConfigWrapper` is eligibile for this `AnalysisRunner`.

        Args:
            ra2ce_input (ConfigWrapper): Configuration desired to run.

        Returns:
            bool: Whether the `ConfigWrapper` can be run or not.
        """
        pass

    def run(self, analysis_config: AnalysisConfigBase) -> None:
        """
        Runs this `AnalysisRunner` with the given analysis configuration.

        Args:
            analysis_config (AnalysisConfigBase): Analysis configuration representation to be run on this `AnalysisRunner`.
        """
        pass
