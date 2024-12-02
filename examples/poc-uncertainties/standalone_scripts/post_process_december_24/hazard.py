from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from event import Event

import matplotlib.pyplot as plt
import seaborn as sns


@dataclass
class Hazard:
    name: str
    list_events: list[Event]

    def add_events(self, df_res: pd.DataFrame):
        df_res_grouped = df_res.groupby("Scenario")
        for scenario, df in df_res_grouped:
            event = Event(name=scenario, frequency=1 / df["return_period"].iloc[0],
                          total_damage=df["Total damage"].values)
            self.list_events.append(event)

    def calc_AAL(self) -> np.array:
        """
        calculate the average annual loss of the hazard for every run

        Returns:
            np.array: an array of len nb_runs with the AAL for every run
        """
        risk_array = self.get_risk_array()
        return risk_array.sum(axis=0)


    def get_damage_array(self, freq: Optional[float] = None):
        """ get a 2D-array with all the damage of all events for every run
        rows: events
        columns: runs

        Possibility to filter per freqency
        """
        # find the minimal length of the total damage arrays
        if freq is not None:
            events = [event for event in self.list_events if event.frequency == freq]
        else:
            events = self.list_events

        min_length = min([len(event.total_damage) for event in events])
        damage_array = np.zeros((len(events), min_length))
        for i, event in enumerate(events):
            damage_array[i, :] = event.total_damage[:min_length]
        return damage_array

    def get_risk_array(self):
        """ get a 2D-array with all the risk of all events for every run
        rows: events
        columns: runs
        """
        min_length = min([len(event.total_damage) for event in self.list_events])
        damage_array = np.zeros((len(self.list_events), min_length))
        for i, event in enumerate(self.list_events):
            damage_array[i, :] = event.total_damage[:min_length] * event.frequency
        return damage_array

    def plot_damage_histogram(self):
        damage_array = self.get_damage_array()
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111)
        sns.histplot(data=damage_array.flatten(), bins=30, ax=ax)
        plt.show()


    def plot_damage_boxplot(self):

        # separate for different frequency
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111)
        sns.boxplot(data=self.get_damage_array().T, ax=ax)
        plt.show()



