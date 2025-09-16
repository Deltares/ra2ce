from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Union

import numpy as np
from IPython.core.pylabtools import figsize
from matplotlib import pyplot as plt
import seaborn as sns
from networkx.algorithms.bipartite.basic import color
from numpy import trapz
from scipy.stats import gaussian_kde

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
    reference_values: Union[list, np.array]
    reference_values_2: Union[list, np.array]

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

    def get_reference_damage(self, ref_id: int = 1) -> float:
        if ref_id == 1:
            return np.mean(self.reference_values) / 1e6
        elif ref_id == 2:
            return np.mean(self.reference_values_2) / 1e6
        else:
            raise NotImplemented("Reference id not implemented")


    def get_reference_AAL(self, ref_id: int = 1) -> float:
        if ref_id == 1:
            return np.sum(self.reference_values * np.array([event.annual_probability for event in self.events]) / 1e6)
        elif ref_id == 2:
            return np.sum(self.reference_values_2 * np.array([event.annual_probability for event in self.events]) / 1e6)
        else:
            raise NotImplemented("Reference id not implemented")

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
                    sort_by_name: bool = False,
                    location: Optional[int] = None,
                    dijkring: Optional[int] = None
                    ) -> np.array:
        """
        Get and filter the data in a array, ready to be plug into plotting function


        """
        if sort_by_name:
            self.events = sorted(self.events, key=lambda x: x.name)
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

        fig = plt.figure(figsize=(18, 4))
        N = self.number_runs

        data = self.filter_data(var, sort_by_return_period, dijkring=dijkring)

        # color the boxplot according to the return period
        orient = 'v'

        # sns.boxplot(data=data, orient=orient, linewidth=2, fill=False, linecolor='black', color='black')


        # color in black and white
        # reverse axis
        plt.boxplot(data, vert=True, patch_artist=False, showfliers=False, widths=0.7, whis=4)

        # sns.swarmplot(data=data,  color="black", alpha=0.5) # dont use for more than 100 runs

        # increase label fontsize
        if orient == 'h':
            plt.xlabel("Scenario")
            # plt.xticks(rotation=45)
            plt.yticks(fontsize=15)
            plt.xlabel("Total damage (Millions EUR)", fontsize=15)
            plt.yticks(range(self.number_events), [event.id for event in self.events], fontsize=10)
        else:
            plt.ylabel("Scenario")
            # plt.xticks(fontsize=15)
            # plt.xticks(rotation=45)
            # plt.ylabel("Total damage (Millions EUR)", fontsize=20)
            plt.yticks(fontsize=20)
            # remove xticks
            plt.xticks([])

            # plt.xticks(range(self.number_events), [event.id for event in self.events], fontsize=10)
        # plt.xticks(range(self.number_events), [event.location for event in self.events])

        # plt.title(f"Boxplot of damages per scenario- {N} runs")
        plt.tight_layout()

        plt.show()

        return

    def plot_histogram(self, var: str):

        plt.figure(figsize=(10, 10))
        data = self.filter_data(var)

       # Show results
        sns.histplot(data.flatten(), bins=60, kde=True)

        if var == 'damage':
            xlabel = "Total damage (Millions EUR)"
            # title = f"Histogram of damages - {self.number_runs} runs"
            # print(f"Reference damage: {self.get_reference_damage()}")
            ref_value = self.get_reference_damage()
            ref_value_2 = self.get_reference_damage(ref_id=2)
        elif var == 'AAL':
            xlabel = "AAL (Millions EUR)"
            # title = f"Histogram of AAL - {self.number_runs} runs"
            ref_value = self.get_reference_AAL()
            ref_value_2 = self.get_reference_AAL(ref_id=2)
        else:
            raise NotImplemented()

        plt.xlabel(xlabel, fontsize=17)
        plt.ylabel("Number of runs", fontsize=17)
        plt.xticks(fontsize=17)
        plt.yticks(fontsize=17)
        # plt.title(title, fontsize=17)

        # give mean and std
        mean = np.mean(data.flatten())
        std = np.std(data.flatten())
        max = np.max(data.flatten())
        plt.axvline(ref_value, color='r', linestyle='--')
        plt.axvline(ref_value_2, color='r', linestyle='--')

        # calc probability of exceedance of ref_value
        prob_exceedance = np.sum(data.flatten() >= ref_value) / len(data.flatten())
        prob_exceedance_2 = np.sum(data.flatten() >= ref_value_2) / len(data.flatten())
        print(f"Probability of exceedance of ref value {ref_value:.2f}: {prob_exceedance:.2%}")
        print(f"Probability of exceedance of ref value 2 {ref_value_2:.2f}: {prob_exceedance_2:.2%}")
        plt.text(0.7, 0.9, f"Mean: {mean:.2f} \n Std: {std:.2f} \n C6 {ref_value:.2f}" , fontsize=17, transform=plt.gca().transAxes)
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
        plt.xlabel("Average Annual Loss (Millions EUR)", fontsize=15)
        plt.ylabel("Frequency", fontsize=15)
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        # plt.title("Cumulative Distribution Function of Average Annual Loss")
        plt.show()


    def plot_EP_spaghetti_plot(self):

        data = self.filter_data('damage')

        all_proba_of_exceedance = []
        all_damage = []

        for run in data:
            order = np.argsort(run)[::-1]
            damage = run[order]
            proba_of_occurence = np.array([event.annual_probability for event in self.events])[order]
            non_proba_of_occurence = 1 - proba_of_occurence
            non_proba_of_exceedance = np.cumprod(non_proba_of_occurence)
            proba_of_exceedance = 1 - non_proba_of_exceedance

            all_proba_of_exceedance.append(proba_of_exceedance)
            all_damage.append(damage)

            plt.plot(damage, proba_of_exceedance, color='black', alpha=0.1)

        # Convert lists to NumPy arrays
        all_proba_of_exceedance = np.array(all_proba_of_exceedance)
        all_damage = np.array(all_damage)

        # Compute 90th percentile for damage at each probability level
        percentile_90 = np.percentile(all_damage, 90, axis=0)
        percentile_mean = np.mean(all_damage, axis=0)

        # plt.plot(percentile_90, np.mean(all_proba_of_exceedance, axis=0), color='red', linewidth=2, label='90th Percentile')
        plt.plot(percentile_mean, np.mean(all_proba_of_exceedance, axis=0), color='blue', linewidth=2, label='Mean')

        # Plot the reference path for ref 1
        order = np.argsort(self.reference_values)[::-1]
        reference_damage = self.reference_values[order]
        proba_of_occurence_ref = np.array([event.annual_probability for event in self.events])[order]
        non_proba_of_occurence_ref = 1 - proba_of_occurence_ref
        non_proba_of_exceedance_ref = np.cumprod(non_proba_of_occurence_ref)
        proba_of_exceedance_ref = 1 - non_proba_of_exceedance_ref
        plt.plot(reference_damage / 1e6, proba_of_exceedance_ref, color='red', linewidth=2, label='Reference C6')

        # Plot the reference path for ref 2
        order2 = np.argsort(self.reference_values_2)[::-1]
        reference_damage2 = self.reference_values_2[order2]
        proba_of_occurence_ref2 = np.array([event.annual_probability for event in self.events])[order2]
        non_proba_of_occurence_ref2 = 1 - proba_of_occurence_ref2
        non_proba_of_exceedance_ref2 = np.cumprod(non_proba_of_occurence_ref2)
        proba_of_exceedance_ref2 = 1 - non_proba_of_exceedance_ref2
        plt.plot(reference_damage2 / 1e6, proba_of_exceedance_ref2, color='red', linestyle='--', linewidth=2, label='Reference C3')

        # Plot confidence interval as a shaded region

        # Add labels and legend
        plt.xlabel("Total damage (Millions EUR)")
        plt.ylabel("Probability of Exceedance")
        plt.legend()

        # ake y axis logarithmic
        plt.yscale('log')
        plt.show()

