from dataclasses import dataclass
from event import ProbabilisticEvent

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

    def from_res_df(self, res_df: pd.DataFrame):
        """
        Create a HazardProbabilisticEventsSet from a pandas DataFrame.

        Args:
            res_df: DataFrame with columns id, name, annual_probability, hazard_map.
        """
        self.events = []
        for i, row in res_df.iterrows():
            self.events.append(ProbabilisticEvent(row["id"], row["name"], row["annual_probability"], row["hazard_map"]))


