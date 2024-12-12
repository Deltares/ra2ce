from dataclasses import dataclass
from typing import Optional

import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns

from event import ProbabilisticEvent
import pandas as pd


@dataclass
class HazardProbabilisticEventsSet:
    """
    Dataclass to hold the a set of probabilistic events for a hazard.
    """
    id: int
    set_name: str
    events: list[ProbabilisticEvent]
    number_events: int
    number_runs: int

    @classmethod
    def from_res_df(cls, res_df: pd.DataFrame, set_name: str):
        """
        Create a HazardProbabilisticEventsSet from a pandas DataFrame.

        Args:
            res_df: DataFrame with columns id, name, annual_probability, hazard_map.
        """

        events = []
        # group by Scenario
        groups = res_df.groupby("Scenario")

        # Ideally we would like to have the same number of runs for all events, but here we take the minimum
        nb_runs = min([len(event[1]["Total damage"]) for event in groups])


        for event_id, event in enumerate(groups, 1):
            event = event[1]
            events.append(ProbabilisticEvent(id=event_id,
                                             hazard_map=event["Scenario"].values[0],
                                             name=event["Scenario"].values[0],
                                             annual_probability=1 / event["return_period"].values[0],
                                             damage=event["Total damage"].values[:nb_runs]))


        return cls(id=1, set_name=set_name, events=events, number_events=len(events), number_runs=nb_runs)

    def get_events_for_return_period(self, return_period: int) -> list[ProbabilisticEvent]:
        """
        Get all events with a certain return period

        Args:
            return_period: Return period of the events to get.

        Returns:
            List of events with the specified return period.
        """
        return [event for event in self.events if event.annual_probability == 1 / return_period]

    def get_damage_array(self, return_period: Optional[int] = None) -> np.ndarray:
        """Get an array of damages for all events and all run.
        Nb of events is number of rows
        Nb of columns is number of runs


                run1 run2 run3 run4 ...
        EV1
        EV2
        ...
        """

        events = self.get_events_for_return_period(return_period) if return_period else self.events
        damage_array = np.zeros((len(events), self.number_runs))
        for event in events:
            damage_array[event.id - 1, :] = event.damage

        return damage_array

    def get_event_frequencies(self)->list[float]:
        """
        Get the annual probability of each event.
        """
        frequencies = [event.annual_probability for event in self.events]
        assert len(frequencies) == self.number_events

        return frequencies

    def get_EAD_vector(self, return_period: Optional[int] = None) -> np.ndarray:
        """
        Get the Expected Annual Damage for each run.
        Size of the vector is equal to the number of runs.
        """
        if return_period is None:
            frequencies = self.get_event_frequencies()
            damage_array = self.get_damage_array()
            # multiply each row by the corresponding event frequency
            EAD = np.sum(np.multiply(damage_array.T, frequencies).T, axis=0)
        else:
            frequencies = 1 / return_period
            damage_array = self.get_damage_array(return_period)
            # multiply each row by the corresponding event frequency
            EAD = np.sum(np.multiply(damage_array.T, frequencies).T, axis=0)

        return EAD

    def plot_violin(self):

        fig = plt.figure(figsize=(10, 10))
        N = self.number_runs

        sns.boxplot(data=self.get_damage_array().T / 1e6)
        sns.swarmplot(data=self.get_damage_array().T / 1e6,  color="black", alpha=0.5)

        plt.xlabel("Scenario")
        plt.xticks(rotation=45)
        plt.ylabel("Total damage (Millions EUR)")
        plt.xticks(range(self.number_events), [event.name for event in self.events])
        plt.title(f"Boxplot of damages per scenario- {N} runs")
        plt.show()

        return