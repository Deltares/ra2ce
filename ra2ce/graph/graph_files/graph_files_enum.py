from enum import Enum


class GraphFilesEnum(Enum):
    BASE_GRAPH = 1
    BASE_GRAPH_HAZARD = 2
    ORIGINS_DESTINATIONS_GRAPH = 3
    ORIGINS_DESTINATIONS_GRAPH_HAZARD = 4
    BASE_NETWORK = 5
    BASE_NETWORK_HAZARD = 6

    def __str__(self) -> str:
        return self.name.lower()
