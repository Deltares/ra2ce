from pathlib import Path
import geopandas as gpd
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

return_period_dict = {"hazard1": 10000,
                      "hazard2": 100000,
                      "hazard3": 1000000,
                      "hazard4": 10000,
                      "hazard5": 100000,
                      "hazard6": 200,
                      "hazard7": 2000,
                      "hazard8": 125,
                      "hazard9": 1250}

hazard_name_dict = {"hazard1": "Nordzee Zuid-Holland",
                    "hazard2": "Nordzee Zuid-Holland",
                    "hazard3": "Nordzee Zuid-Holland",
                    "hazard4": "Doorbrak bij Ijmuiden",
                    "hazard5": "Doorbrak bij Ijmuiden",
                    "hazard6": "Lek (downstream Hagestein)",
                    "hazard7": "Lek (downstream Hagestein)",
                    "hazard8": "Lek (upstream Hagestein)",
                    "hazard9": "Lek (upstream Hagestein)"}


def plot_histogram_by_hazard(df):
    fig = plt.figure(figsize=(10, 10))
    N = int(len(df))
    df.groupby("Hazard")["Total damage"].plot(kind="hist", bins=40, alpha=0.6, legend=True)
    plt.xlabel("Total damage (Millions EUR)")
    plt.ylabel("Frequency")
    plt.title(f"Histogram of damages per hazard- {N} runs")
    plt.show()


def plot_histogram_all(df):
    fig = plt.figure(figsize=(10, 10))
    N = int(len(df))
    plt.hist(df["Total damage"], bins=50, )
    plt.xlabel("Total damage (Millions EUR)")
    plt.ylabel("Frequency")
    plt.title(f"Histogram damages all hazards - {N} runs")
    plt.show()

def plot_histogram_stacked(df):
    # Group data by hazard and aggregate total damage
    grouped_data = df.groupby('Hazard')['Total damage'].apply(list).reset_index()

    # Colors for each hazard
    # colors = ['brown', 'purple', 'red', 'green', 'orange', 'blue', 'cyan', 'magenta', 'yellow']
    colors = sns.color_palette("husl", n_colors=len(grouped_data))  # Use 'husl' palette

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))

    # # Loop through each hazard and plot the KDE
    for i, row in grouped_data.iterrows():
        hazard = row['Hazard']
        impact_values = row['Total damage']

        # Estimate the density of the damage values
        kde = gaussian_kde(impact_values)
        impact_range = np.linspace(0, max(impact_values) + 1, 100)
        density = kde(impact_range)

        # Scale the density values for better visibility
        scaling_factor = 3
        density_scaled = density * scaling_factor

        # Plot the density as a filled area
        ax.fill_between(impact_range, i, i + density_scaled, color=colors[i % len(colors)], alpha=0.7, label=hazard)

        # Optionally, plot a vertical dashed line for the mean damage value
        ax.axvline(np.mean(impact_values), color=colors[i % len(colors)], linestyle='dotted',
                   ymax=(i + 1) / len(grouped_data))

    # Set y-ticks and labels to match the hazards
    ax.set_yticks(np.arange(len(grouped_data)))
    ax.set_yticklabels(grouped_data['Hazard'])

    # Set axis labels
    ax.set_xlabel('Total Damage (Millions EUR)')
    ax.set_ylabel('Hazard Type')
    ax.set_title('Total Damage Distribution by Hazard Category')

    # Display the legend
    ax.legend(title='Hazard Type', bbox_to_anchor=(1.05, 1), loc='upper left')

    # Display the plot
    plt.tight_layout()
    plt.show()


def plot_box_plot_by_hazard(df):
    fig = plt.figure(figsize=(10, 10))
    N = int(len(df))
    sns.boxplot(data=df, x="Hazard", y="Total damage")
    plt.xlabel("Hazard")
    plt.ylabel("Total damage (Millions EUR)")
    plt.title(f"Boxplot of damages per hazard- {N} runs")
    plt.show()

def plot_box_plot_by_scenario_1(array):
    fig = plt.figure(figsize=(10, 10))
    N = int(len(df))
    sns.boxplot(data=df, x="Scenario", y="Total damage")
    # draw vertical lines between each hazard
    sns.swarmplot(data=df, x="Scenario", y="Total damage", color="black", alpha=0.5)
    plt.xlabel("Scenario")
    # rotate x labels
    plt.xticks(rotation=45)
    plt.ylabel("Total damage (Millions EUR)")
    plt.title(f"Boxplot of damages per scenario- {N} runs")
    plt.show()

def plot_box_plot_by_scenario(df):
    fig = plt.figure(figsize=(20, 10))
    N = int(len(df))
    # plot the boxplot but order them by hazard
    sns.boxplot(data=df, x="Scenario", y="Total damage", order=df['Scenario'].unique())

    # draw vertical separation lines between hazards
    plt.axvline(48.5, color='black', linestyle='--')
    plt.axvline(42.5, color='black', linestyle='--')
    plt.axvline(29.55, color='black', linestyle='--')
    plt.axvline(19.55, color='black', linestyle='--')
    plt.axvline(16.55, color='black', linestyle='--')
    plt.axvline(13.55, color='black', linestyle='--')
    plt.axvline(4.55, color='black', linestyle='--')

    plt.xlabel("Scenario")
    # rotate x labels
    plt.xticks(rotation=45)
    plt.ylabel("Total damage (Millions EUR)")
    plt.title(f"Boxplot of damages per scenario- {N} runs")
    plt.show()


def plot_histogram_risk(df):
    fig = plt.figure(figsize=(10, 10))
    N = int(len(df))
    df["AAL"] = df["Total damage"] / df["return_period"]
    plt.hist(df["AAL"], bins=50, )
    plt.xlabel("Average Annual Loss (Millions EUR)")
    plt.ylabel("Frequency")
    plt.title(f"Histogram of Average Annual Loss - {N} runs")
    plt.show()

def plot_damage_vs_return_period(df):
    # plot the mean damage vs return period
    fig = plt.figure(figsize=(10, 10))
    N = int(len(df))
    mean_damage = df.groupby("return_period")["Total damage"].mean().reset_index()
    damage_95 = df.groupby("return_period")["Total damage"].quantile(0.95).reset_index()
    damage_5 = df.groupby("return_period")["Total damage"].quantile(0.05).reset_index()

    # add 0,0 point to the plot
    mean_damage = mean_damage.append({"return_period": 0, "Total damage": 0}, ignore_index=True)
    damage_5 = damage_5.append({"return_period": 0, "Total damage": 0}, ignore_index=True)
    damage_95 = damage_95.append({"return_period": 0, "Total damage": 0}, ignore_index=True)
    mean_damage = mean_damage.sort_values("return_period")
    damage_5 = damage_5.sort_values("return_period")
    damage_95 = damage_95.sort_values("return_period")

    # plot
    plt.plot(mean_damage["return_period"], mean_damage["Total damage"])
    plt.fill_between(mean_damage["return_period"], damage_5["Total damage"], damage_95["Total damage"], alpha=0.2)

    plt.xlabel("Return period (years)")
    plt.ylabel("Total damage (Millions EUR)")
    plt.title(f"Mean damage vs return period - {N} runs")
    # add legend
    plt.legend(["Mean damage", "5th and 95th percentile"])
    plt.show()

