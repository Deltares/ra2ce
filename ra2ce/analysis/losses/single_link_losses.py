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
        return SingleLinkRedundancy(self.analysis_input)
