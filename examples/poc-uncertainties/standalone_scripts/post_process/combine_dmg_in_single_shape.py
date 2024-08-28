from pathlib import Path
import geopandas as gpd

# path of the event results. We combine all the runs in a single shapefile per event!
path = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\output_monte_carlo\output_13_08_test\event6")

path_link_based_combined_results = path.joinpath("damage_link_based_combined.gpkg")
path_segmented_combined_results = path.joinpath("damage_segmented_combined.gpkg")
segmented = False

gdf_link_based_combined = gpd.read_file(path_link_based_combined_results)

if segmented:
    gdf_segmented_combined = gpd.read_file(path_segmented_combined_results)

run_id = 1

# iterate through all the scenarios and run adn concatenate the columns "dam_EV1_al" from all the dataframe inot the combined dataframe
for scenario in path.iterdir():
    if not scenario.is_dir():
        continue
    scenario_name = scenario.name

    for run in scenario.iterdir():
        print(run_id)
        name = scenario_name + "_" + str(run_id)
        gdf_link = gpd.read_file(run.joinpath("Manual_damage_link_based.gpkg"))
        gdf_segmented = gpd.read_file(run.joinpath("Manual_damage_segmented.gpkg"))
        gdf_link_based_combined[name] = gdf_link["dam_EV1_al"]
        if segmented:
            gdf_segmented_combined[name] = gdf_segmented["dam_EV1_al"]
        run_id += 1

print("Writing results...")
gdf_link_based_combined.to_file(path_link_based_combined_results, driver="GPKG")
if segmented:
    gdf_segmented_combined.to_file(path_segmented_combined_results, driver="GPKG")  # Takes way too long.
print("Done!")


