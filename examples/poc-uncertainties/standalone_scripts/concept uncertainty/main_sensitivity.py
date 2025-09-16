from pathlib import Path
import pandas as pd
import numpy as np
from SALib import ProblemSpec

from event import ProbabilisticEvent
from hazard_probabilitistic_set import HazardProbabilisticEventsSet
import SALib
from SALib.analyze import sobol


result_csv = Path(
    r"c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\output_new_damage_cuvres\results_new_ALL.csv"
    # r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\res\results500-700.csv"
)
# samples = np.load(r'C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\samples_1280.npy')
# samples = np.load(r'c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2025 SITO\data\case_damage\samples_1280.npy')



sp = ProblemSpec(
    {
        'num_vars': 3,
        'names': [
            'h',
            'k',
            'S'
        ],
        'bounds': [
            [500, 100],  # final height
            [1, 15],  # stiffness
            [0, 0.293560379208524]  # cost scaling factor
        ],
        'dists': [
            'norm',
            'unif',
            'lognorm'
        ],
        "outputs": ['damage']

    }
)

df = pd.read_csv(result_csv)

print(df)
outputs = df.to_numpy().transpose()[0]
print(outputs)
print(len(samples), len(outputs))

sp.set_samples(samples)
sp.set_results(outputs)
sp.analyze_sobol()
print(sp)


import matplotlib.pyplot as plt


axes = sp.plot()
axes[0].set_yscale('log')
fig = plt.gcf()  # get current figure
fig.set_size_inches(10, 4)
plt.tight_layout()
plt.show()