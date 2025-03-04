from pathlib import Path
import geopandas as gpd
import re
# path of the event results. We combine all the runs in a single shapefile per event!
path_dir = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\res"
)

result_csv = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\res"
)


#Get all columns with format 'dam_EV35_al' the digit being arbitrary. Use regex to match the pattern, exclude dam_EV15_al_segments

pattern = re.compile(r"dam_EV\d+_al")


def extract_number(filename):
    match = re.search(r'_(\d+)$', filename.stem)  # Extract number at the end
    return int(match.group(1)) if match else float('inf')  # Handle unexpected cases

# Get all files and sort them numerically
sorted_files = sorted(path_dir.iterdir(), key=lambda f: extract_number(f))

data_primary = []
data_secondary = []
data_tertiary = []
data_highway = []
for index, run in enumerate(sorted_files, 1):
    print(run.name)

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

            #filter for rows  with highway type primary
            gdf_primary = gdf[gdf['highway'].isin(['primary', 'primary_link'])]
            gdf_secondary = gdf[gdf['highway'].isin(['secondary', 'secondary_link'])]
            gdf_tertiary = gdf[gdf['highway'].isin(['tertiary', 'tertiary_link'])]
            gdf_highway = gdf[gdf['highway'].isin(['motorway', 'motorway_link', 'trunk', 'trunk_link'])]
            row_primary = gdf_primary[matched_cols].sum().tolist()
            row_secondary = gdf_secondary[matched_cols].sum().tolist()
            row_tertiary = gdf_tertiary[matched_cols].sum().tolist()
            row_highway = gdf_highway[matched_cols].sum().tolist()

        else:
            row_primary = []  # Handle the case where no columns match
            row_secondary = []
            row_tertiary = []
            row_highway = []


        data_primary.append(row_primary)  # Append the row to the data list
        data_secondary.append(row_secondary)
        data_tertiary.append(row_tertiary)
        data_highway.append(row_highway)

#save as csv
import pandas as pd
df_primary = pd.DataFrame(data_primary)
df_secondary = pd.DataFrame(data_secondary)
df_tertiary = pd.DataFrame(data_tertiary)
df_highway = pd.DataFrame(data_highway)
df_primary.to_csv(result_csv.joinpath('primary.csv'), index=False)
df_secondary.to_csv(result_csv.joinpath('secondary.csv'), index=False)
df_tertiary.to_csv(result_csv.joinpath('tertiary.csv'), index=False)
df_highway.to_csv(result_csv.joinpath('highway.csv'), index=False)