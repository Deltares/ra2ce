from pathlib import Path
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

path_output = Path(r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\output_monte_carlo\output_10_10")

hazard = "hazard1"


data_df = pd.read_csv(path_output.joinpath("damage_result.csv"), sep=";")
N = int(len(data_df))


data_df["AAL"] = data_df["Total damage"] / data_df["return_period"]

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111)
plt.hist(data_df["AAL"], bins=50, )
plt.show()


# Plot CDF
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111)
sns.ecdfplot(data=data_df, x="AAL", ax=ax)
plt.show()