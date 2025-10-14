
from ra2ce.analysis.analysis_config_data.single_link_redundancy_config_data import (
    SingleLinkRedundancyConfigData,
)

from .adaptation_config_data import AdaptationConfigData
from .base_link_losses_config_data import (
    MultiLinkLossesConfigData,
    SingleLinkLossesConfigData,
)
from .base_origin_destination_config_data import (
    MultiLinkOriginClosestDestinationConfigData,
    MultiLinkOriginDestinationConfigData,
    OptimalRouteOriginClosestDestinationConfigData,
    OptimalRouteOriginDestinationConfigData,
)
from .damages_config_data import DamagesConfigData
from .equity_config_data import EquityConfigData
from .losses_analysis_config_data_protocol import LossesAnalysisConfigDataProtocol
from .multi_link_redundancy_config_data import MultiLinkRedundancyConfigData

LossesConfigDataTypes: list[type[LossesAnalysisConfigDataProtocol]] = [
    SingleLinkLossesConfigData,
    MultiLinkLossesConfigData,
    SingleLinkRedundancyConfigData,
    MultiLinkRedundancyConfigData,
    MultiLinkOriginDestinationConfigData,
    MultiLinkOriginClosestDestinationConfigData,
    OptimalRouteOriginDestinationConfigData,
    OptimalRouteOriginClosestDestinationConfigData,
    EquityConfigData
]