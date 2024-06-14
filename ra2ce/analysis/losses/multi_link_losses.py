from ra2ce.analysis.losses.losses_base import LossesBase
from ra2ce.analysis.losses.multi_link_redundancy import MultiLinkRedundancy


class MultiLinkLosses(LossesBase):
    """
    Calculates the multi-link redundancy losses of a NetworkX graph.

    The function removes all links of a variable that have a minimum value
    of min_threshold. For each link it calculates the alternative path, if any available.
    This function only removes one group at the time and saves the data from removing that group.

    This class is based on the LossesBase abstract base class.
    Don't override other methods than _get_criticality_analysis.
    """

    def _get_criticality_analysis(self) -> MultiLinkRedundancy:
        return MultiLinkRedundancy(self.analysis_input)
