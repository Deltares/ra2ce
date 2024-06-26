from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class WeighingAnalysisProtocol(Protocol):
    edge_data: dict[str, Any]

    def get_current_value(self) -> float:
        """
        Gets the current distance/time of the edge.
        If the edge has no distance/time attribute, it is calculated and added to the edge.

        Returns:
            float: Current distance/time value.
        """
