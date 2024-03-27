from pathlib import Path
import pandas as pd
import geopandas as gpd

# set the required parameters
cloud_output_folder = Path('/data')

event_names = [folder.stem for folder in cloud_output_folder.iterdir() if folder.is_dir()]
# save as a .py script
fid_column = "rfid"

for i, event_name in enumerate(event_names):
    output_path = cloud_output_folder / event_name / "output" / "multi_link_redundancy" / "example_redundancy_multi.gpkg"
    output_gdf = gpd.read_file(output_path)
    
    # Define the mapping of EV1_ column names to event_name
    column_mapping = {"diff_length": f"{event_name}_diff_length", "connected": f"{event_name}_connected"}
    output_gdf = output_gdf.rename(columns=column_mapping)
    output_gdf.fillna(0, inplace=True)


    if i == 0:
        # create the base gdf that aggregate all results
        result_gdf = output_gdf
    else:
        filtered_output_gdf = output_gdf[[fid_column, f"{event_name}_diff_length", f"{event_name}_connected"]]
        result_gdf = pd.merge(
            result_gdf,
            filtered_output_gdf,
            left_on=fid_column,
            right_on=fid_column,
        )

gdf = result_gdf

gdf.to_file('/output/result_q2_gdf.geojson', driver="GeoJSON")
gdf.to_feather('/output/result_q2_gdf.feather')