from dataclasses import dataclass


@dataclass
class AdaptationOptionConfigData:
    """
    Reflects all possible settings that an adaptation option might contain.
    The id should be unique and is used to determine the location of the input and output files.
    This dataclass does not implement `AnalysisConfigDataProtocol` because it is not an analysis itself.
    """

    id: str = ""
    name: str = ""
    construction_cost: float = 0.0
    construction_interval: float = 1000.0
    maintenance_cost: float = 0.0
    maintenance_interval: float = 1000.0    
