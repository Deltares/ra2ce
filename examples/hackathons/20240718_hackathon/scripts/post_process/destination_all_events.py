from pathlib import Path
import geopandas as gpd
# make pretty map
import folium
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

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

final_destinations_gdf = gpd.GeoDataFrame()
final_destinations_gdf["d_id"] = destinations_gdf["d_id"]
final_destinations_gdf["geometry"] = destinations_gdf["geometry"]
final_destinations_gdf["category"] = destinations_gdf["category"]
final_destinations_gdf = final_destinations_gdf[final_destinations_gdf["category"] == category]

res_dict = {}
# for event in events[6:8]:
for event in events:
    print(event.stem)
    path_dir = path_results.joinpath(event)
    path_with_hazard_OD_result = path_dir.joinpath("origin_closest_destination_optimal_routes_with_hazard.gpkg")

    # Load data
    optimal_routes_with_hazard_gdf = gpd.read_file(path_with_hazard_OD_result)
    # Get the all the unique destinations:
    destinations = optimal_routes_no_hazard_gdf["destination"].unique()
    # keep only selected category
    destinations_gdf = destinations_gdf[destinations_gdf["category"] == category]


    # Step 1: clean destination gdf to account for combined destinations like: "B_5,B_6"
    temp_gdf = gpd.GeoDataFrame()
    for dest in destinations:
        if "," in dest:
            dests = dest.split(",")
            temp_gdf = temp_gdf.append(destinations_gdf[destinations_gdf["d_id"] == dests[0]])
            # rename the destination id to the combined destination id
            temp_gdf.loc[temp_gdf["d_id"] == dests[0], "d_id"] = dest

        else:
            temp_gdf = temp_gdf.append(destinations_gdf[destinations_gdf["d_id"] == dest])

    destinations_gdf = temp_gdf

    # Step 2:
    total_number_of_population_no_hazard = 0
    total_number_of_population_with_hazard = 0
    for destination in destinations:
        optimal_routes_per_destination_no_hazard_gdf = optimal_routes_no_hazard_gdf[
            optimal_routes_no_hazard_gdf['destination'] == destination]  # filter on destination B4
        optimal_routes_per_destination_with_hazard_gdf = optimal_routes_with_hazard_gdf[
            optimal_routes_with_hazard_gdf['destination'] == destination]  # filter on destination B4
        # get the id of all the origins associated with the destination
        list_origins_id_no_hazard = optimal_routes_per_destination_no_hazard_gdf['origin'].unique()
        list_origins_id_with_hazard = optimal_routes_per_destination_with_hazard_gdf['origin'].unique()

        gdf_origins = gpd.read_file(path_origins)
        # filter the origins gdf to only include the origins associated with the destination B4
        gdf_origins_filtered_no_hazard = gdf_origins[gdf_origins['o_id'].isin(list_origins_id_no_hazard)]
        gdf_origins_filtered_with_hazard = gdf_origins[gdf_origins['o_id'].isin(list_origins_id_with_hazard)]

        # count the column POPULATION:
        nb_population_no_hazard = int(gdf_origins_filtered_no_hazard['POPULATION'].sum())
        nb_population_with_hazard = int(gdf_origins_filtered_with_hazard['POPULATION'].sum())

        total_number_of_population_no_hazard += nb_population_no_hazard
        total_number_of_population_with_hazard += nb_population_with_hazard
        diff_population = nb_population_no_hazard - nb_population_with_hazard
        if nb_population_no_hazard == 0:
            relative_diff_population = 0
        else:
            relative_diff_population = round(diff_population / nb_population_no_hazard * 100, 1)

        # add count population to destination gdf
        destinations_gdf.loc[destinations_gdf['d_id'] == destination, 'population_no_hazard'] = nb_population_no_hazard
        destinations_gdf.loc[
            destinations_gdf['d_id'] == destination, 'population_with_hazard'] = nb_population_with_hazard
        destinations_gdf.loc[destinations_gdf['d_id'] == destination, 'diff_population'] = diff_population
        destinations_gdf.loc[
            destinations_gdf['d_id'] == destination, 'relative_diff_population'] = relative_diff_population

    print("No hazard: ", total_number_of_population_no_hazard)
    print("With hazard: ", total_number_of_population_with_hazard)
    print("population with no access: ", total_number_of_population_no_hazard - total_number_of_population_with_hazard)
    final_destinations_gdf[f"{event.stem}_pop_with_hazard"] = destinations_gdf["population_with_hazard"]


    res_dict[event.stem] = {"no_hazard": total_number_of_population_no_hazard,
                            "with_hazard": total_number_of_population_with_hazard,
                            "diff": total_number_of_population_no_hazard - total_number_of_population_with_hazard}



    # Step 3: create a map

    base_map = folium.Map(location=[-19.84505, 34.8734], zoom_start=9, tiles="CartoDB dark_matter")

    destinations_group = folium.FeatureGroup(name='Destinations')
    for _, row in destinations_gdf.iterrows():
        if row['population_with_hazard'] == 0:
            color = 'red'
            hover_strings = "<b> Destination</b> {row['d_id']} <br>" \
                            "<b>Population no hazard:</b> {row['population_no_hazard']} <br>" \
                            "<b>Population with hazard:</b> {row['population_with_hazard']} <br>" \
                            "UNREACHABLE"

            hover = folium.Popup(hover_strings, max_width=300)
        else:
            if row['population_no_hazard'] - row['population_with_hazard'] > 0:
                color = 'green'
                # hover= f'Popultation no hazard {row["population_no_hazard"]}, <br> population with hazard {row["population_with_hazard"]}'
                hover_strings = f"<b>Destination</b> {row['d_id']} <br>" \
                                f"<b>Population no hazard:</b> {row['population_no_hazard']} <br>" \
                                f"<b>Population with hazard:</b> {row['population_with_hazard']} <br>" \
                                f"<b>Decrease: -</b> {row['diff_population']} <br>" \
                                f"<b>Relative decrease: -</b> {row['relative_diff_population']} %<br>"
                hover = folium.Popup(hover_strings, max_width=300)
            else:
                if row['diff_population'] == 0:
                    color = 'green'
                else:
                    color = 'yellow'
                # hover = f'Population no hazard {row["population_no_hazard"]}, population with hazard {row["population_with_hazard"]}'
                hover_strings = f"<b>Destination</b> {row['d_id']} <br>" \
                                f"<b>Population no hazard:</b> {row['population_no_hazard']} <br>" \
                                f"<b>Population with hazard:</b> {row['population_with_hazard']} <br>" \
                                f"<b>Increase: +</b> {abs(row['diff_population'])} <br>" \
                                f"<b>Relative increase: +</b> {abs(row['relative_diff_population'])} %<br>"
                hover = folium.Popup(hover_strings, max_width=300)

        folium.CircleMarker(
            location=[row['geometry'].y, row['geometry'].x],
            radius=5,
            color=color,
            fill=True,

            popup=hover
        ).add_to(base_map)

    # filter origins

    # destination_display = "B_323"
    # # destination_display = "B_496,B_498"
    # optimal_routes_per_destination_no_hazard_gdf = optimal_routes_no_hazard_gdf[
    #     optimal_routes_no_hazard_gdf['destination'] == destination_display]  # filter on destination B4
    # optimal_routes_per_destination_with_hazard_gdf = optimal_routes_with_hazard_gdf[
    #     optimal_routes_with_hazard_gdf['destination'] == destination_display]  # filter on destination B4
    # # get the id of all the origins associated with the destination
    # list_origins_id_no_hazard = optimal_routes_per_destination_no_hazard_gdf['origin'].unique()
    # list_origins_id_with_hazard = optimal_routes_per_destination_with_hazard_gdf['origin'].unique()
    #
    # # filter the origins gdf to only include the origins associated with the destination B4
    # gdf_origins_filtered_no_hazard = gdf_origins[gdf_origins['o_id'].isin(list_origins_id_no_hazard)]
    # gdf_origins_filtered_with_hazard = gdf_origins[gdf_origins['o_id'].isin(list_origins_id_with_hazard)]
    #
    # # gdf_origins_filtered_no_hazard.explore(m=base_map, color='green', marker_kwds={'radius': 5})
    # gdf_origins_filtered_no_hazard.explore(m=base_map, color='white', marker_kwds={'radius': 2})
    #
    # # Create a feature group for target_optimal_routes_with_hazard_gdf
    # target_optimal_routes_with_hazard_map = folium.FeatureGroup(name="Optimal Routes With Hazard")
    # optimal_routes_with_hazard_gdf_temps = optimal_routes_with_hazard_gdf[
    #     optimal_routes_with_hazard_gdf['destination'] == destination_display]
    # optimal_routes_with_hazard_gdf_temps.explore(m=target_optimal_routes_with_hazard_map, color='red',
    #                                              line_kwds={'weight': 2})
    # target_optimal_routes_with_hazard_map.add_to(base_map)

    # save map
    base_map.save(path_dir.joinpath(f"map_{category}_{event.stem}.html"))



#save res in csv
df = pandas.DataFrame(res_dict)
df.to_csv(path_results.joinpath("results.csv"))


#save gdf destinations
print(final_destinations_gdf)
print(final_destinations_gdf.columns)
print((final_destinations_gdf.dtypes=='geometry').sum()>1)
final_destinations_gdf.to_file(path_results.joinpath("destinations_events.gpkg"), driver="GPKG")
final_destinations_gdf.to_file(path_results.joinpath("destinations_events.geojson"), driver="GeoJSON")



