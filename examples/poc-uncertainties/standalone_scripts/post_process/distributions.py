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

matplotlib = True
plotly = False
event_1 = path.joinpath("event1/")
event_2 = path.joinpath("event2/")
event_3 = path.joinpath("event3/")
gdf_1 = gpd.read_file(event_1.joinpath("damage_link_res.gpkg"))
gdf_2 = gpd.read_file(event_2.joinpath("damage_link_res.gpkg"))
gdf_3 = gpd.read_file(event_3.joinpath("damage_link_res.gpkg"))

run_names_1 = [col for col in gdf_1.columns if col.startswith("scenario")]
run_names_2 = [col for col in gdf_2.columns if col.startswith("scenario")]
run_names_3 = [col for col in gdf_3.columns if col.startswith("scenario")]


print(run_names_1)

# stop

# sum all the rows:
damages_1 = gdf_1[run_names_1].sum(axis=0).to_numpy() / 1e6
damages_2 = gdf_2[run_names_2].sum(axis=0).to_numpy() / 1e6
damages_3 = gdf_3[run_names_3].sum(axis=0).to_numpy() / 1e6

# plot histogram
if matplotlib:
    plt.hist(damages_1, bins=100, label="EV1: Nordzee Zuid-Holland_10000")
    plt.hist(damages_2, bins=100, label="EV2: Nordzee Zuid-Holland_100000")
    plt.hist(damages_3, bins=100, label="EV3: Nordzee Zuid-Holland_1000000")
    plt.xlabel("Damages (million euros)")
    plt.ylabel("Frequency")
    plt.title("Histogram of damages")

    plt.legend()
    # plt.show()

    # n=100
    #
    # h,e = np.histogram(damages_1, bins=100, density=True)
    # x = np.linspace(e.min(), e.max())
    # plt.figure(figsize=(8,6))
    # plt.bar(e[:-1], h, width=np.diff(e), ec='k', align='edge', label='histogram')
    #
    # # plot the real KDE
    # kde = sts.gaussian_kde(damages_1)
    # plt.plot(x, kde.pdf(x), c='C1', lw=8, label='KDE')


    # plot the KDE
    plt.legend()
    plt.show()

    plt.show()


if plotly:
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=damages_1, name="EV1: Nordzee Zuid-Holland_10000"))
    fig.add_trace(go.Histogram(x=damages_2, name="EV2: Nordzee Zuid-Holland_100000"))
    fig.add_trace(go.Histogram(x=damages_3, name="EV3: Nordzee Zuid-Holland_1000000"))

    fig.update_layout(
        title_text='Histogram of damages',
        xaxis_title_text='Damages (million euros)',
        yaxis_title_text='Frequency',
        bargap=0.2,
        bargroupgap=0.1
    )

    fig.show()