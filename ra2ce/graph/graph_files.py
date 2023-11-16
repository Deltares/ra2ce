from pathlib import Path
from typing import Optional

from attr import dataclass


@dataclass
class GraphFiles:
    base_graph: Optional[Path] = None
    base_graph_hazard: Optional[Path] = None
    origins_destinations_graph: Optional[Path] = None
    origins_destinations_graph_hazard: Optional[Path] = None
    base_network: Optional[Path] = None
    base_network_hazard: Optional[Path] = None
