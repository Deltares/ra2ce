from pathlib import Path
import geopandas as gpd
# make pretty map
import folium
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
# import tabulate
import pandas
# from IPython.display import display


path_results = Path(r'P:\moonshot2-casestudy\RA2CE_HACKATHON_JULY\results')

# loop over all directiories and get names:

events = [x for x in path_results.iterdir() if x.is_dir()]
event = "TC_0064"
category = "hospital"
print(events)

# load data shared for all events
event_0_dir = events[0]
path_no_hazard_OD_result = event_0_dir.joinpath("origin_closest_destination_optimal_routes_without_hazard.gpkg")
path_origins = event_0_dir.joinpath("origin_closest_destination_origins.gpkg")
path_destinations = event_0_dir.joinpath("origin_closest_destination_destinations.gpkg")
optimal_routes_no_hazard_gdf = gpd.read_file(path_no_hazard_OD_result)
origins_gdf = gpd.read_file(path_origins)
destinations_gdf = gpd.read_file(path_destinations)
destinations = optimal_routes_no_hazard_gdf["destination"].unique()

p = path_results.joinpath("destinations_events.gpkg")
gdf_destinations = gpd.read_file(p)

# get all columns names except d_id and geometry
columns = gdf_destinations.columns
columns = [c for c in columns if c not in ["d_id", "geometry", "category", 'pop_without_hazard']]
for c in columns:
    gdf_destinations[c[0:7] + 'diff'] = gdf_destinations[c] - gdf_destinations["pop_without_hazard"]

# count number of columns with positive values
gdf_destinations["count_pos"] = gdf_destinations[columns].gt(0).sum(axis=1)
# count numer of columns with negative values
gdf_destinations["count_neg"] = gdf_destinations[columns].lt(0).sum(axis=1)



final_gdf = gpd.GeoDataFrame()
final_gdf["geometry"] = gdf_destinations["geometry"]
final_gdf["d_id"] = gdf_destinations["d_id"]
final_gdf["category"] = gdf_destinations["category"]

final_gdf["count_pos"] = gdf_destinations["count_pos"]
final_gdf["count_neg"] = gdf_destinations["count_neg"]
final_gdf["pop_without_hazard"] = gdf_destinations["pop_without_hazard"]

a = final_gdf.explore()

print(final_gdf)
# a.show_in_browser()



