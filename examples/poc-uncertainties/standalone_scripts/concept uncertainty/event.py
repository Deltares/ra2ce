from pathlib import Path
from dataclasses import dataclass


@dataclass
class ProbabilisticEvent:
    id: int
    name: str
    annual_probability: float  # maybe should be renamed annual_frequency or use return period for simplification.
    location: int  # specific to this use case
    dijkring: int  # specific to thisnuse case
    hazard_map: Path

    # result
    damage: list[float] # list of damage for all the runs of the even

    @property
    def return_period(self):
        return round(1 / self.annual_probability)


