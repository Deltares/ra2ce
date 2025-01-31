from dataclasses import dataclass
from typing import Optional

import numpy as np
from IPython.core.pylabtools import figsize
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
    def from_res_df_2024(cls, res_df: pd.DataFrame, set_name: str):
        """
        Create a HazardProbabilisticEventsSet from a pandas DataFrame.
        Old logic from 2024

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

    def get_events_for_location(self, location: int) -> list[ProbabilisticEvent]:
        return [event for event in self.events if event.location == location]

    def get_events_for_dijkring(self, dijkring_id: int) -> list[ProbabilisticEvent]:
        return [event for event in self.events if event.dijkring == dijkring_id]

    def get_damage_array(self, return_period: Optional[int] = None) -> np.ndarray:
        """Get an array of damages for all events and all run.
        Nb of events is number of rows
        Nb of columns is number of runs


                run1 run2 run3 run4  ...  runN
        EV1
        EV2
        ...
        EVk

        Args:
            return_period: Return period of the events to get. If None, return all events.

        """

        if return_period is not None:
            events = self.get_events_for_return_period(return_period)
        else:
            events = self.events
        damage_array = np.array([event.damage for event in events])

        return damage_array

    def get_event_frequencies(self) -> list[float]:
        """
        Get the annual probability of each event.
        """
        frequencies = [event.annual_probability for event in self.events]

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

    def filter_data(self, var: str,
                    sort_by_return_period: bool = False,
                    sort_by_dijkring: bool = False,
                    sort_by_location: bool = False,
                    location: Optional[int] = None,
                    dijkring: Optional[int] = None
                    ) -> np.array:
        """
        Get and filter the data in a array, ready to be plug into plotting function


        """
        if sort_by_return_period:
            self.events = sorted(self.events, key=lambda x: x.annual_probability)

        if sort_by_dijkring:
            self.events = sorted(self.events, key=lambda x: x.dijkring)

        if sort_by_location:
            self.events = sorted(self.events, key=lambda x: x.location)

        if location is not None:
            self.events = self.get_events_for_location(location)
            self.number_events = len(self.events)

        if dijkring is not None:
            self.events = self.get_events_for_dijkring(dijkring)
            self.number_events = len(self.events)

        if var == "damage":
            data = self.get_damage_array().T / 1e6
        elif var == "AAL":
            data = self.get_EAD_vector() / 1e6
        else:
            raise NotImplemented("Not implemented yet")
        return data

    def plot_violin(self, var: str,
                    sort_by_return_period: bool = False,
                    sort_by_dijkring: bool = False,
                    sort_by_location: bool = False,
                    location: Optional[int] = None,
                    dijkring: Optional[int] = None
                    ):

        plt.figure(figsize=(10, 10))
        N = self.number_runs

        data = self.filter_data(var, sort_by_return_period, dijkring=dijkring)

        sns.boxplot(data=data)
        # sns.swarmplot(data=data,  color="black", alpha=0.5) # dont use for more than 100 runs


        plt.xlabel("Scenario")
        plt.xticks(rotation=45)
        plt.ylabel("Total damage (Millions EUR)")
        plt.xticks(range(self.number_events), [event.id for event in self.events])
        # plt.xticks(range(self.number_events), [event.location for event in self.events])
        plt.title(f"Boxplot of damages per scenario- {N} runs")
        plt.show()

        return

    def plot_histogram(self, var: str):

        plt.figure(figsize=(10, 10))
        data = self.filter_data(var)

        sns.histplot(data.flatten(), bins=30, kde=True)

        if var == 'damage':
            label = "Total damage (Millions EUR)"
        elif var == 'AAL':
            label = "AAL (Millions EUR)"
        else:
            raise NotImplemented()
        plt.xlabel(label)
        plt.ylabel("Number of runs")
        plt.title(f"Total damage - {self.number_runs} runs")
        plt.show()

    def plot_histogram_events(self):

        for event in self.events:
            plt.figure(figsize=(10, 10))
            plt.hist(event.damage / 1e6, bins=30, )
            plt.xlabel("Total damage (Millions EUR)")
            plt.ylabel("Frequency")
            plt.title(f"Histogram damages {event.name} - {self.number_runs} runs")
            plt.show()

    def plot_CDF_AAL(self):
        EAD = self.get_EAD_vector() / 1e6
        EAD = np.sort(EAD)
        sns.ecdfplot(EAD, complementary=True, log_scale=(False, True))

        # y = np.arange(len(EAD)) / float(len(EAD))
        # plt.plot(EAD, y)
        plt.xlabel("Average Annual Loss (Millions EUR)")
        plt.ylabel("Probability")
        plt.title("Cumulative Distribution Function of Average Annual Loss")
        plt.show()