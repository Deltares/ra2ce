from dataclasses import dataclass
import numpy as np

@dataclass
class Event:
    name: str
    frequency: float # this is the annual frequency of the event (=annual probability of occurence of event, or simpler terms the inverse of the return period of the event
    total_damage: np.array # this is the total damage caused by the event for all simulations

    def nb_runs(self):
        return len(self.total_damage)
