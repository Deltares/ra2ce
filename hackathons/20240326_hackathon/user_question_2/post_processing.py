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
    output_path = (
        cloud_output_folder
        / event_name
        / "output"
        / "multi_link_redundancy"
        / "example_redundancy_multi.gpkg"
    )
    output_gdf = gpd.read_file(output_path)

    # Column mapping
    column_mapping_overlay = {
        event_wl_column: f"{event_name}_" + aggregate_wl_column,
        event_fraction_column: f"{event_name}_fr",
    }
    overlay_output_gdf = overlay_output_gdf.rename(columns=column_mapping_overlay)

    column_mapping = {
        "diff_length": f"{event_name}_diff_length",
        "connected": f"{event_name}_connected",
    }
    output_gdf = output_gdf.rename(columns=column_mapping)
    output_gdf.fillna(0, inplace=True)

    if i == 0:
        # create the base gdf that aggregate all results
        overlay_result_gdf = overlay_output_gdf
        redundancy_result_gdf = output_gdf
    else:
        filtered_overlay_output_gdf = overlay_output_gdf[
            [fid_column, f"{event_name}_" + aggregate_wl_column, f"{event_name}_fr"]
        ]
        overlay_result_gdf = pd.merge(
            overlay_result_gdf,
            filtered_overlay_output_gdf,
            left_on=fid_column,
            right_on=fid_column,
        )

        filtered_output_gdf = output_gdf[
            [fid_column, f"{event_name}_diff_length", f"{event_name}_connected"]
        ]
        redundancy_result_gdf = pd.merge(
            redundancy_result_gdf,
            filtered_output_gdf,
            left_on=fid_column,
            right_on=fid_column,
        )


# Ensure output directory exists
_output_path = Path("/output")
_output_path.mkdir()

overlay_result_gdf.to_file("/output/overlay_result.geojson", driver="GeoJSON")
overlay_result_gdf.to_feather("/output/overlay_result.feather")

redundancy_result_gdf.to_file("/output/redundancy_result.geojson", driver="GeoJSON")
redundancy_result_gdf.to_feather("/output/redundancy_result.feather")
