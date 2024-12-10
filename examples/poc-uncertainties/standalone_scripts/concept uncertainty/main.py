from pathlib import Path
import pandas as pd
from hazard_probabilitistic_set import HazardProbabilisticEventsSet


path_res = Path(r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\Monte Carlo results")

df = pd.read_csv(path_res.joinpath("damage_result.csv"), sep=";")

print(df.head(5))

# filter out the events
df_1 = df[df["Hazard"].isin(["hazard1, hazard2, hazard3"])]
print(df_1.head(5))


haz_set = HazardProbabilisticEventsSet(path_res.joinpath("hazard_set.csv"))


