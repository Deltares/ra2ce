from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class WeighingAnalysisProtocol(Protocol):
    edge_data: dict[str, Any]

    def calculate_current_value(self) -> float:
        """
        Calculates the current distance/time of the edge.

        Returns:
            float: Current distance/time value.
        """

    def calculate_alternative_value(self, alt_dist: float) -> float:
        """
        Calculates the alternative distances/times of the edge.

        Args:
            alt_dist (float): Provided alternative distance/time.

        Returns:
            float: Corrected alternative distance/time value.
        """
