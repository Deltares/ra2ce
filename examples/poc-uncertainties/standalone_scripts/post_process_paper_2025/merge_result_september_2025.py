from pathlib import Path
import geopandas as gpd
import re

from numpy import mean
import pandas as pd

# path of the event results. We combine all the runs in a single shapefile per event!
path_dir = Path(
    r"c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\output_new_damage_cuvres"
)

result_csv = Path(
    r"c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\output_new_damage_cuvres\results_new_ALLL.csv"
)


#Get all columns with format 'dam_EV35_al' the digit being arbitrary. Use regex to match the pattern, exclude dam_EV15_al_segments

pattern = re.compile(r"dam_EV\d+_al")
pattern_huizinga = re.compile(r"dam_EV\d+_HZ")
#
#
# def extract_number(filename):
#     match = re.search(r'_(\d+)$', filename.stem)  # Extract number at the end
#     return int(match.group(1)) if match else float('inf')  # Handle unexpected cases
#
# # Get all files and sort them numerically
# sorted_files = sorted(path_dir.iterdir(), key=lambda f: extract_number(f))
#
# print(sorted_files)
#
#
# data = []
# for index, run in enumerate(sorted_files, 1):
#     print(run.name)
#
#     run =  run.joinpath('damages', "Manual_damage_link_based.gpkg")
#
#     if run.is_file():
#         if 'segmented' in run.name:
#             continue
#         if run.suffix != ".gpkg":
#             continue
#
#
#         gdf = gpd.read_file(run)
#
#         # Filter columns that match the pattern and do not end with "segments"
#         matched_cols = [col for col in gdf.columns if pattern.match(col) and not col.endswith("segments")]
#
#         # Use a vectorized approach to sum matching columns
#         if matched_cols:
#             row = gdf[matched_cols].sum().tolist()  # Sum each column and convert to list
#         else:
#             row = []  # Handle the case where no columns match
#
#         data.append(row)  # Append the row to the data list
#
# #save as csv
#
# df = pd.DataFrame(data)
# df.to_csv(result_csv, index=False)


ref_file = Path(r"c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\paper\work_dir_augus_2025\output\damages\Manual_damage_c3_link_based.gpkg")
gdf = gpd.read_file(ref_file)
print(gdf)
print(gdf.columns)
# Filter columns that match the pattern and do not end with "segments"
matched_cols = [col for col in gdf.columns if pattern.match(col) and not col.endswith("segments")]

# Use a vectorized approach to sum matching columns
damage = gdf[matched_cols].sum().tolist()  # Sum each column and convert to list
df = pd.DataFrame(damage)
df.to_csv(Path(
    r"c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\output_new_damage_cuvres\results_ref_C3.csv"
), index=False)
print(damage)
print(mean(damage) / 1e6)