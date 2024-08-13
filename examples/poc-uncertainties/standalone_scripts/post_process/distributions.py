from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt


path = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\output_monte_carlo\output_13_08_test/")

event_1 = path.joinpath("event1/")
event_2 = path.joinpath("event2/")
event_3 = path.joinpath("event3/")
gdf_1 = gpd.read_file(event_1.joinpath("damage_link_res.gpkg"))
gdf_2 = gpd.read_file(event_2.joinpath("damage_link_res.gpkg"))
gdf_3 = gpd.read_file(event_3.joinpath("damage_link_res.gpkg"))

run_names_1 = [col for col in gdf_1.columns if col.startswith("scenario")]
run_names_2 = [col for col in gdf_2.columns if col.startswith("scenario")]
run_names_3 = [col for col in gdf_3.columns if col.startswith("scenario")]


# sum all the rows:

damages_1 = gdf_1[run_names_1].sum(axis=0).to_list()
damages_2 = gdf_2[run_names_2].sum(axis=0).to_list()
damages_3 = gdf_3[run_names_3].sum(axis=0).to_list()
print(damages_1)

# plot histogram
plt.hist(damages_1, bins=100, label="EV1: Nordzee Zuid-Holland_10000")
plt.hist(damages_2, bins=100, label="EV2: Nordzee Zuid-Holland_100000")
plt.hist(damages_3, bins=100, label="EV3: Nordzee Zuid-Holland_1000000")
plt.xlabel("Damages")
plt.ylabel("Frequency")
plt.title("Histogram of damages")

plt.legend()
plt.show()
