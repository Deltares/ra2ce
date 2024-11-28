from pathlib import Path
import geopandas as gpd
import pandas as pd

path_output = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\projects\RACE\RA2CE Proba 2024\output_monte_carlo\output_10_10")
df_store = pd.read_csv(path_output.joinpath("damage_result.csv"), sep=";")

hazard = "hazard8"
return_period_dict = {"hazard1": 10000,
                      "hazard2": 100000,
                      "hazard3": 1000000,
                      "hazard4": 10000,
                      "hazard5": 100000,
                      "hazard6": 200,
                      "hazard7": 2000,
                      "hazard8": 125,
                      "hazard9": 1250}



def add_data_to_db(folder_res, hazard_name: str):
    data_output = []
    for folder in folder_res.iterdir():
        if not folder.is_dir():
            continue

        for file in folder.iterdir():
            if file.name == "Manual_damage_link_based.gpkg":
                print(file)
                gdf = gpd.read_file(file)
                total_damage = gdf["dam_EV1_al"].sum()
                flood_map_name = folder.stem.split("_")[-1]
                data_output.append({"Hazard": hazard_name, "Scenario": flood_map_name, "Total damage": total_damage,
                                    "return_period": return_period_dict[hazard_name]})

    df = pd.DataFrame(data_output)
    df.to_csv(path_output.joinpath(f"damage_results_{hazard_name}.csv"), index=False, sep=";")
    return data_output


def add_all_hazard_to_db(path_hazard_output):
    data_to_write = []
    for folder in path_hazard_output.iterdir():
        if not folder.is_dir():
            continue
        hazard_name = folder.stem
        print("Processing: ", hazard_name)
        data_to_write.extend(add_data_to_db(folder, hazard_name))
        # write to csv
    df = pd.DataFrame(data_to_write)
    df.to_csv(path_hazard_output.joinpath(f"damage_result.csv"), index=False, sep=";")



def concat_df_and_save_to_csv(hazard_name: str):
    df = pd.read_csv(path_output.joinpath(f"damage_results_{hazard_name}.csv"), sep=";")
    df_res = pd.concat([df_store, df])
    df_res.to_csv(path_output.joinpath("damage_result.csv"), index=False, sep=";")



# data_to_write = []
# path_res = path_output.joinpath(hazard)
# data_to_write.extend(add_data_to_db(path_res, hazard))
# # # add_all_hazard_to_db(path_output)
# #
# # # write to csv
# df = pd.DataFrame(data_to_write)
# df.to_csv(path_output.joinpath(f"damage_results_{hazard}.csv"), index=False, sep=";")




concat_df_and_save_to_csv("hazard5")