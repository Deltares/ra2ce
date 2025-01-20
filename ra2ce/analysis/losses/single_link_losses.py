from ra2ce.analysis.losses.losses_base import LossesBase
from ra2ce.analysis.losses.single_link_redundancy import SingleLinkRedundancy


class SingleLinkLosses(LossesBase):
    """
    Calculates the single-link redundancy losses of a NetworkX graph.
    This is the function to analyse roads with a single link disruption and an alternative route.

    This class is based on the LossesBase abstract base class.
    Don't override other methods than _get_criticality_analysis.
    """

    def _get_criticality_analysis(self) -> SingleLinkRedundancy:
        # Provide the graph file with hazard overlay if it's result is consumed by a losses analysis.
        self.analysis_input.graph_file = self.analysis_input.graph_file_hazard
        return SingleLinkRedundancy(self.analysis_input)
