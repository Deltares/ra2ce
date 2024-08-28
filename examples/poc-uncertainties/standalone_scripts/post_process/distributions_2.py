from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import scipy.stats as sts
import numpy as np
import matplotlib.pyplot as plt
from plotly import graph_objects as go
path = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\output_monte_carlo\output_13_08_test/")

matplotlib = False
plotly = True
event_1 = path.joinpath("event1/")
event_2 = path.joinpath("event2/")
event_3 = path.joinpath("event3/")
event_6 = path.joinpath("event6/")
gdf_1 = gpd.read_file(event_6.joinpath("damage_link_res.gpkg"))

run_names_1 = [col for col in gdf_1.columns if col.startswith("scenario")]

# get all unique scenario names from 'scenario_18367_1':
# print(run_names_1)
unique_scenario_names = set([name.split("_")[1] for name in run_names_1])
print(unique_scenario_names) #   {'5025', '18367', '565', '18377', '18372', '571', '5028', '18375', '18369', '603'}
names = [col for col in gdf_1.columns if "5025" in col]


damages_1 = gdf_1[run_names_1].sum(axis=0).to_numpy() / 1e6
damagege = gdf_1[names].sum(axis=0).to_numpy() / 1e6


fig, axs = plt.subplots(6, 2)
col = 0
row = 0
for scenario in unique_scenario_names:
    # make a new subplot for each scenario
    print(row, col)
    if row == 6:
        row = 0
        col =1
    names = [col for col in gdf_1.columns if scenario in col]
    damagege = gdf_1[names].sum(axis=0).to_numpy() / 1e6
    axs[row,col].hist(damages_1, color="grey", alpha=0.5, bins=30, label="All")
    axs[row,col].hist(damagege, color="red", bins=5, label=f"{scenario}")
    axs[row, col].legend()

    row +=1







plt.show()
