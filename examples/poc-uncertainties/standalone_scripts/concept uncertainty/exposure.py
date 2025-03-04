import re
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import geopandas as gpd
path =  Path(r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\res\Manual_damage_link_based_10.gpkg")

gdf = gpd.read_file(path)
print(list(gdf.columns))
print(gdf['length'].sum() / 1e3)
ev_columns = [col for col in gdf.columns if re.match(r"dam_EV\d+_al", col) and not col.endswith("segments")]
ev_columns_fr = [col for col in gdf.columns if re.match(r"EV\d+_fr", col) and not col.endswith("segments")]
print(ev_columns)

# multiply column length with EV1_fr and create a new column. Do it for all ev_columns

exposed_length_array = []
for ev_column in ev_columns_fr:
    gdf[ev_column + "_length"] = gdf["length"] * gdf[ev_column]
    # print(gdf[ev_column + "_length"].sum() / 1e3)
    exposed_length_array.append(gdf[ev_column + "_length"].sum())

# sns.swarmplot(y=exposed_length_array)
# plt.show()


valid_rows = (gdf[ev_columns] <= 0).all(axis=1)

# print(valid_rows)
# cumulative_length = gdf.loc[valid_rows, "length"].sum()
# print(cumulative_length / 1e3)


#######


order_combi = [13514, 13516, 13518, 13528, 13529, 13530, 13531, 13532, 13534, 13535, 13536, 13537, 13538, 13539, 13540,
               13541, 13542, 13543, 13545, 13546, 13548, 13550, 13554, 13555, 13970, 13971, 13974, 13975, 13979, 13980,
               19035, 19036, 19037, 19038, 19039, 19040, 19041, 19042, 19043, 19044, 19045, 19046, 19047, 19048, 19049,
               19050, 19051, 19052, 19053, 19054, 19055, 19056, 19057, 19058, 19059, 19060, 19061, 19062, 19063, 19064,
               19121, 19122, 19726, 19727, 19728, 19729, 19730, 19731, 19732, 21052, 21053, 21054, 21055, 21056, 21057,
               21058, 21068, 21069, 810, 813]


scenario_data = pd.read_excel(
    Path(r'C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\scenario_definition.xlsx'))
scenario_data =  scenario_data.set_index("Scenario ID").loc[order_combi].reset_index()

ev_columns2 = [col for col in gdf.columns if re.match(r"EV\d+_ma", col) and not col.endswith("segments")]
print(ev_columns)

proba_occurence = scenario_data['prob_cond'].to_numpy()
# P(R)=1−(1−p1​⋅P(R∣D1​))(1−p2​⋅P(R∣D2​))(1−p3​⋅P(R∣D3​))
# the conditional probaility is either 1 if EVi_ma > 0 or 0 if EVi_ma <= 0
# the probability of occurence is the annual probability of the event
# the probability of non-occurence is 1 - the annual probability of the event
# the probability of non-occurence is 1 - the annual probability of the event
gdf['prob'] = 1 - np.prod([(1 - proba_occurence[i] * (gdf[ev_columns2[i]] > 0)) for i in range(len(ev_columns2))], axis=0)












