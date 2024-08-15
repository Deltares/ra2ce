from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import stats
import scipy.stats as sts
import numpy as np
import matplotlib.pyplot as plt
from plotly import graph_objects as go
import plotly.express as px


path = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\output_monte_carlo\output_13_08_test/")

matplotlib = False
plotly = True
event_1 = path.joinpath("event1/")
event_2 = path.joinpath("event2/")
event_3 = path.joinpath("event3/")
gdf_1 = gpd.read_file(event_3.joinpath("damage_link_res.gpkg"))

run_names_1 = [col for col in gdf_1.columns if col.startswith("scenario")]
print(run_names_1)
# get all unique scenario names from 'scenario_18367_1':
# print(run_names_1)
unique_scenario_names = set([name.split("_")[1] for name in run_names_1])
print(unique_scenario_names)  # {'5025', '18367', '565', '18377', '18372', '571', '5028', '18375', '18369', '603'}
names = [col for col in gdf_1.columns if "5025" in col]

damages_1 = gdf_1[run_names_1].sum(axis=0).to_numpy() / 1e6
damagege = gdf_1[names].sum(axis=0).to_numpy() / 1e6

fig = go.Figure()
print(damages_1)
# fig.add_trace(go.Histogram(x=run_names_1,
#                            y=damages_1,
#                            name="All",
#                            marker_color="grey",
#                            xbins=dict(
#                                size=0.1
#                            ),
#
#
#
#
#                            ))

df = pd.DataFrame(data={"run_names": run_names_1, "damages": damages_1})
# add scenario columns based on run_names
df["scenario"] = df["run_names"].apply(lambda x: x.split("_")[1])

fig = px.scatter(df, x="run_names", y="damages", color="scenario")
# can also do


fig.show()
# save the figure
fig.write_html("distribution_3_Event2.html")
