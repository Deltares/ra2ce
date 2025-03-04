from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from SALib import ProblemSpec

from event import ProbabilisticEvent
from hazard_probabilitistic_set import HazardProbabilisticEventsSet
import SALib
from SALib.analyze import sobol


result_csv = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\res\results_1024.csv"
    # r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\res\results500-700.csv"
)

samples = np.load(r'C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\samples_1280.npy')

print(samples)
parameters = ['h', 'k', 'S']

# Create subplots for histograms
fig, axes = plt.subplots(1, 3, figsize=(12, 4))

for i, ax in enumerate(axes):
    ax.hist(samples[:, i], bins=30, alpha=0.7, color='b', edgecolor='black')
    ax.set_title(f"Distribution of {parameters[i]}")
    ax.set_xlabel(parameters[i])
    ax.set_ylabel("Frequency")

plt.tight_layout()
plt.show()


###### Pairwise contour plots of the KDE

df = pd.DataFrame(samples, columns=parameters)

# Create contour plots for each pair
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Define parameter pairs for contour plots
pairs = [(0, 1), (0, 2), (1, 2)]  # (h, k), (h, S), (k, S)

for i, (x_idx, y_idx) in enumerate(pairs):
    sns.kdeplot(
        x=df.iloc[:, x_idx],
        y=df.iloc[:, y_idx],
        fill=True,
        cmap="Blues",
        thresh=0.05,
        levels=20,
        ax=axes[i]
    )
    axes[i].set_xlabel(parameters[x_idx])
    axes[i].set_ylabel(parameters[y_idx])
    axes[i].set_title(f"Density Contour: {parameters[x_idx]} vs {parameters[y_idx]}")

plt.tight_layout()
plt.show()




# plot input distributions of the samples:

sns.pairplot(df, diag_kind="kde", corner=True)

# Set title
plt.suptitle("Pairwise Scatter Plots of Input Samples", y=1.02)

# Show the plot
plt.show()

