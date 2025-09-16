from pathlib import Path
import re
import geopandas as gpd
import numpy as np
import pandas as pd


path_dir = Path(
    r"c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\output_new_damage_cuvres"
)

result_csv = Path(
    r"c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\output_new_damage_cuvres\res_AAL.gpkg"



)

scenario_data = pd.read_excel(
    Path(
        r'c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\paper\scenario_definition.xlsx'))



order_hazards_Waal = [13514, 13516, 13518, 13528, 13529, 13530, 13531, 13532, 13534, 13535, 13536, 13537, 13538, 13539,
                      13540, 13541, 13542, 13543, 19053, 19054, 19055, 19056, 19057, 19058, 19059, 19060, 19061, 19062,
                      19063, 19064, 19726, 19727, 19728, 19729, 19730, 19731, 19732, 21052, 21058, 21069, 810, 813]

order_hazards_Lek = [13545, 13546, 13548, 13550, 13554, 13555, 13970, 13971, 13974, 13975, 13979, 13980, 19035, 19036,
                     19037, 19038, 19039, 19040, 19041, 19042, 19043, 19044, 19045, 19046, 19047, 19048, 19049, 19050,
                     19051, 19052, 19121, 19122, 21053, 21054, 21055, 21056, 21057, 21068]

order_combi = [13514, 13516, 13518, 13528, 13529, 13530, 13531, 13532, 13534, 13535, 13536, 13537, 13538, 13539, 13540,
               13541, 13542, 13543, 13545, 13546, 13548, 13550, 13554, 13555, 13970, 13971, 13974, 13975, 13979, 13980,
               19035, 19036, 19037, 19038, 19039, 19040, 19041, 19042, 19043, 19044, 19045, 19046, 19047, 19048, 19049,
               19050, 19051, 19052, 19053, 19054, 19055, 19056, 19057, 19058, 19059, 19060, 19061, 19062, 19063, 19064,
               19121, 19122, 19726, 19727, 19728, 19729, 19730, 19731, 19732, 21052, 21053, 21054, 21055, 21056, 21057,
               21058, 21068, 21069, 810, 813]

data_waal = scenario_data[scenario_data['Rivier'] == 'Waal']
data_lek = scenario_data[scenario_data['Rivier'] == 'Lek']
data_combi = scenario_data
data_waal = data_waal.set_index("Scenario ID").loc[order_hazards_Waal].reset_index()
data_lek = data_lek.set_index("Scenario ID").loc[order_hazards_Lek].reset_index()
data_combi = data_combi.set_index("Scenario ID").loc[order_combi].reset_index()



#Get all columns with format 'dam_EV35_al' the digit being arbitrary. Use regex to match the pattern, exclude dam_EV15_al_segments

pattern = re.compile(r"dam_EV\d+_al")
pattern_huizinga = re.compile(r"dam_EV\d+_HZ")


def extract_number(filename):
    match = re.search(r'_(\d+)$', filename.stem)  # Extract number at the end
    return int(match.group(1)) if match else float('inf')  # Handle unexpected cases

# Get all files and sort them numerically
sorted_files = sorted(path_dir.iterdir(), key=lambda f: extract_number(f))

print(sorted_files)


probabilities = np.array(data_combi['prob_cond'])

data = []

# write a gpkg file with the calculated AAL per link

for index, run in enumerate(sorted_files, 1):
    print(run.name)
    # if index > 10:
    #     continue

    run =  run.joinpath('damages', "Manual_damage_link_based.gpkg")

    if run.is_file():
        if 'segmented' in run.name:
            continue
        if run.suffix != ".gpkg":
            continue


        gdf = gpd.read_file(run)

        # Filter columns that match the pattern and do not end with "segments"
        matched_cols = [col for col in gdf.columns if pattern.match(col) and not col.endswith("segments")]



        # Use a vectorized approach to sum matching columns
        if matched_cols:
            row = (gdf[matched_cols] * probabilities).to_numpy()
            data.append(row.sum(axis=1))  # Sum each column and convert to list


data = np.array(data).T

gdf_result = gdf[['geometry', 'highway', 'length']]
gdf_result['AAL_mean'] = data.mean()
gdf_result['AAL_min'] = data.min(axis=1)
gdf_result['AAL_max'] = data.max(axis=1)
gdf_result['AAL_p10'] = np.percentile(data, 10, axis=1)
gdf_result['AAL_p90'] = np.percentile(data, 90, axis=1)
gdf_result['AAL_std'] = data.std(axis=1)
gdf_result['AAL_median'] = np.median(data, axis=1)
gdf_result['AAL_sum'] = data.sum(axis=1)
gdf_result.to_file(result_csv, driver="GPKG")




