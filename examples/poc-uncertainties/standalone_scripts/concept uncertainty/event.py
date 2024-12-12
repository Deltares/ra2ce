from pathlib import Path
from dataclasses import dataclass


@dataclass
class ProbabilisticEvent:
    id: int
    name: str
    annual_probability: float  # maybe should be renamed annual_frequency or use return period for simplification.
    hazard_map: Path

    # result
    damage: list[float] # list of damage for all the runs of the event


