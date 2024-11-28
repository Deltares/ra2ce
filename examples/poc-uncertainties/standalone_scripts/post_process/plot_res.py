from pathlib import Path
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from plot_makers import *

path_output = Path(r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\output_monte_carlo\output_10_10")

hazard = "hazard1"


data_df = pd.read_csv(path_output.joinpath("damage_result.csv"), sep=";")
# sort by hazard
data_df = data_df.sort_values("Hazard")
N = int(len(data_df))

#remove low values below 10k network damage and convert into millions
data_df = data_df[data_df["Total damage"] > 1000000]
data_df["Total damage"] = data_df["Total damage"] / 1e6

# Filter Keep only hazard1 and hazard2:
# data_df = data_df[data_df["Hazard"].isin(["hazard6", "hazard7"])]
# data_df = data_df[data_df["Hazard"].isin(["hazard8", "hazard9"])]



plot_histogram_all(data_df)
plot_histogram_by_hazard(data_df)
plot_histogram_stacked(data_df)
plot_box_plot_by_hazard(data_df)
plot_box_plot_by_scenario(data_df)
plot_histogram_risk(data_df)
df2 = data_df[data_df["Hazard"].isin(["hazard1", "hazard2", "hazard3"])]
# df2 = data_df[data_df["Hazard"].isin(["hazard8", "hazard9"])]
plot_damage_vs_return_period(df2)





