from pathlib import Path

import geopandas as gpd
import pandas as pd

# set the required parameters
cloud_output_folder = Path("/data")

event_names = [
    folder.stem for folder in cloud_output_folder.iterdir() if folder.is_dir()
]
# save as a .py script
aggregate_wl = "max"  # this we should get from network_config or analysis_config

aggregate_wls = {"max": "ma", "mean": "me", "min": "mi"}

aggregate_wl_column = aggregate_wls[aggregate_wl]
event_wl_column = "EV1_" + aggregate_wl_column
event_fraction_column = "EV1_fr"
fid_column = "rfid"

for i, event_name in enumerate(event_names):
    overlay_output_path = (
        cloud_output_folder
        / event_name
        / "static"
        / "output_graph"
        / "base_graph_hazard_edges.gpkg"
    )
    overlay_output_gdf = gpd.read_file(overlay_output_path)

    # Define the mapping of EV1_ column names to event_name
    column_mapping = {
        event_wl_column: f"{event_name}_" + aggregate_wl_column,
        event_fraction_column: f"{event_name}_fr",
    }
    overlay_output_gdf = overlay_output_gdf.rename(columns=column_mapping)

    if i == 0:
        # create the base gdf that aggregate all results
        result_gdf = overlay_output_gdf
    else:
        filtered_overlay_output_gdf = overlay_output_gdf[
            [fid_column, f"{event_name}_" + aggregate_wl_column, f"{event_name}_fr"]
        ]
        result_gdf = pd.merge(
            result_gdf,
            filtered_overlay_output_gdf,
            left_on=fid_column,
            right_on=fid_column,
        )

gdf = result_gdf

gdf.to_file("/output/result_gdf.geojson", driver="GeoJSON")
gdf.to_feather("/output/result_gdf.feather")
