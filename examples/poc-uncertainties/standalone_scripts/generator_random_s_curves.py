from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


# folder where the vulnerability curves are saved
path_folder = Path(r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\vulnerability_curves")

def logistic_function_scaled(x, k, x0):
    logistic_value = 1 / (1 + np.exp(-k * (x - x0)))
    logistic_0 = 1 / (1 + np.exp(k * x0))
    return logistic_value - logistic_0


x = np.linspace(0, 1, 11)

plt.figure(figsize=(10, 6))
for i in range(40):

    final_height = np.random.normal(100, 10)  # final height for which we reach 100% damage
    k = np.random.uniform(1, 15)  # Random steepness between 1 and 15
    # k=-1
    x0 = np.random.uniform(0.4, 0.6)  # Random midpoint between 0.25 and 0.75

    y = logistic_function_scaled(x, k, x0)
    y = y / max(y)  # Normalize to range [0, 1]

    plt.plot(x * final_height, y, label=f'k={k:.2f}, x0={x0:.2f}', linewidth=4)

    # generate vulnerability curves as csv:
    df = pd.DataFrame({'depth': x * final_height, 'damage': y})
    df.to_csv(path_folder / f'vulnerability_curve_{i}.csv', index=False)


# increase font size:
# plt.legend(fontsize=15)
plt.xlabel('water height (m)', fontsize=15)
plt.ylabel('% damage', fontsize=15)
plt.title('Random S-curves (Logistic Distribution)')
plt.grid(True)
plt.show()


