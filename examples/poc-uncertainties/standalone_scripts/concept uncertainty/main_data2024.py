from pathlib import Path
import pandas as pd
from hazard_probabilitistic_set import HazardProbabilisticEventsSet


path_res = Path(r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\Monte Carlo results")

df = pd.read_csv(path_res.joinpath("damage_result.csv"), sep=";")


# filter out the events
df_1 = df[df["Hazard"].isin(["hazard1", "hazard2", "hazard3"])]

haz_set_A = HazardProbabilisticEventsSet.from_res_df_2024(df[df["Hazard"].isin(["hazard1", "hazard2", "hazard3"])],
                                                          "Coastal hazard")
haz_set_B = HazardProbabilisticEventsSet.from_res_df_2024(df[df["Hazard"].isin(["hazard4", "hazard5"])], "Ijmuiden")
haz_set_C = HazardProbabilisticEventsSet.from_res_df_2024(df[df["Hazard"].isin(["hazard6", "hazard7"])], "Lek1")
haz_set_D = HazardProbabilisticEventsSet.from_res_df_2024(df[df["Hazard"].isin(["hazard8", "hazard9"])], "Lek2")

# print(haz_set_D)

array =  haz_set_D.get_EAD_vector()
print(array)


