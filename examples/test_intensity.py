import geopandas as gpd

# Read in the data
# gdf = gpd.read_file(r"C:\Users\groen_fe\OneDrive - Stichting Deltares\1_Projects\Moonshot_5\network_with_all_data_edges.gpkg")

# gdf.columns

# gdf["morn_intens_h"].sum()
# gdf["even_intens_h"].sum()

# gdf_high = gdf.loc[gdf["morn_capac_min_intens"] >= 100] # estimate
# dict_lanes_ratio = {}

# for lane in gdf_high["lanes_new"].unique():
#     dict_lanes_ratio[lane] = gdf_high.loc[gdf_high["lanes_new"] == lane, "morn_intens_h"].sum() / gdf_high.loc[gdf_high["lanes_new"] == lane, "capacity"].sum()

# gdf.rename(columns={"capacity": "capacity_initial"}, inplace=True)

# gdf.loc[gdf["morn_capac_min_intens"] >= 100, "capacity"] = gdf.loc[gdf["morn_capac_min_intens"] >= 100, "morn_capac_min_intens"] 
# gdf.loc[gdf["morn_capac_min_intens"] < 100, "capacity"] = gdf.loc[gdf["morn_capac_min_intens"] < 100].apply(lambda x: (1 - dict_lanes_ratio[x["lanes_new"]]) * x["capacity_initial"], axis=1)

# gdf.to_file(r"C:\Users\groen_fe\OneDrive - Stichting Deltares\1_Projects\Moonshot_5\network_with_all_data_edges_updated_capacity.gpkg", driver="GPKG")


from ra2ce.common.io.readers.graph_pickle_reader import GraphPickleReader
from ra2ce.graph.exporters.multi_graph_network_exporter import MultiGraphNetworkExporter
from pathlib import Path

od_graph = Path(r"C:\Users\groen_fe\OneDrive - Stichting Deltares\1_Projects\Moonshot_5\network_with_all_data.p")
graph = GraphPickleReader().read(od_graph)

# gdf["osmid"] = gdf["osmid"].astype(str)
for e in graph.edges(data=True, keys=True):
    # graph[e[0]][e[1]][e[2]]["capacity"] = gdf.loc[gdf["osmid"] == str(e[-1]["osmid"]), 'capacity'].values[0]
    graph[e[0]][e[1]][e[2]]["capacity"] = e[-1]["capacity"] * 0.5

# for n in graph.nodes(data=True):
#     if "od_id" in n[-1]:
#         if "NL" in n[-1]["od_id"]:
#             demand = graph.nodes[n[0]]["hourly_containers"]
#             graph.nodes[n[0]]["demand"] = demand / 1000 * 672
#         if "DE" in n[-1]["od_id"]:
#             demand = graph.nodes[n[0]]["hourly_containers"]
#             graph.nodes[n[0]]["demand"] = - round((demand / 1000 * 672), 0)
#             if n[0] == 1243218667:
#                 graph.nodes[n[0]]["demand"] = - round((demand / 1000 * 672), 0) + 1

# [n for n in graph.nodes()]
# sum([n[-1]["demand"] for n in graph.nodes(data=True) if "od_id" in n[-1]])

exporter = MultiGraphNetworkExporter(basename="network_with_all_data_0_5_capacity", export_types=["shp", "pickle"])
exporter.export_to_shp(output_dir=Path(r"c:\Users\groen_fe\OneDrive - Stichting Deltares\1_Projects\Moonshot_5"), export_data=graph)
exporter.export_to_pickle(output_dir=Path(r"c:\Users\groen_fe\OneDrive - Stichting Deltares\1_Projects\Moonshot_5"), export_data=graph)
