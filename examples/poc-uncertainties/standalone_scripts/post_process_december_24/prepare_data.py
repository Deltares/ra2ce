from pathlib import Path

import numpy as np
import pandas as pd
from hazard import Hazard

path_unsorted_results = Path(r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\output_monte_carlo\output_10_10")
df_results = pd.read_csv(path_unsorted_results.joinpath("damage_result.csv"), sep=";")
print(df_results)

Haz_A = Hazard(name="Coast", list_events=[])
Haz_B = Hazard(name="Ijmuiden", list_events=[])
Haz_C = Hazard(name='Lek 1', list_events=[])
Haz_D = Hazard(name='Lek 2', list_events=[])


# group by hazard
df_results_grouped = df_results.groupby("Hazard")
# create a sub dataframe for each hazard
for hazard, df in df_results_grouped:
    print(hazard)
    if hazard in ["hazard1", "hazard2", "hazard3"]:
        Haz_A.add_events(df)
    elif hazard in ["hazard4", "hazard5"]:
        Haz_B.add_events(df)
    elif hazard in ["hazard6", "hazard7"]:
        Haz_C.add_events(df)
    elif hazard in ["hazard8", "hazard9"]:
        Haz_D.add_events(df)
    else:
        raise ValueError("Hazard not found")

print(Haz_C)
for event in Haz_C.list_events:
    print(event.name, event.nb_runs(), 1 / event.frequency)

for event in Haz_D.list_events:
    print(event.name, event.nb_runs(), 1 / event.frequency)


Haz_C.get_damage_array()
AAL_A = Haz_A.calc_AAL()
AAL_B = Haz_B.calc_AAL()
AAL_C = Haz_C.calc_AAL()
AAL_D = Haz_D.calc_AAL()

alpha_C = AAL_C.sum() /  ( AAL_C.sum() + AAL_D.sum())
alpha_D = AAL_D.sum() /  ( AAL_C.sum() + AAL_D.sum())
print(alpha_C, alpha_D)

Haz_C.plot_damage_boxplot()
Haz_C.plot_damage_histogram()
STOP

# plot histo of AAL with seaborn
import matplotlib.pyplot as plt
import seaborn as sns
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111)
sns.histplot(data=AAL_A, bins=10, ax=ax)
# sns.histplot(data=AAL_D, bins=10, ax=ax)

plt.show()


# concatenate horizontally all AAL arrays

all_AAL = np.concatenate([Haz_A.calc_AAL(), Haz_B.calc_AAL(), Haz_C.calc_AAL(), Haz_D.calc_AAL()], axis=0)
ax = sns.histplot(data=all_AAL, bins=30)
plt.show()

# plot CDF
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111)
sns.ecdfplot(data=AAL_D, ax=ax)
plt.show()




