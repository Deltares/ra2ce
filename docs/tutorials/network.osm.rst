Network from OSM download
=========================


This tutorial shows how to download and configure a road network from OpenStreetMap (OSM) and process it using the RA2CE library.

Step 1. Import the Required Packages
------------------------------------

.. code-block:: python

    from pathlib import Path
    import geopandas as gpd
    from shapely.geometry.polygon import Polygon

    from ra2ce.network import RoadTypeEnum
    from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
    from ra2ce.network.network_config_data.network_config_data import NetworkSection, NetworkConfigData
    from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
    from ra2ce.ra2ce_handler import Ra2ceHandler



Step 2. Define a region of interest
-----------------------------------

The first step is to define a region of interest for which we want to retrieve the road network. In this example, we will use a bounding box around a specific area.
The region of interest must be represented as a GIS polygon saved as a geojson file. As a user, you have the freedom to create this polygon using any GIS software of your choice.
For example, you can use QGIS, a popular open-source GIS software, to create and save the polygon as a geojson file.

In this example, we create a bounding box using the shapely library and save it as a geojson file using geopandas.

Indicate the path to the root directory of your project and to the network shapefile. We recommend to follow the structure shown in the `Getting Started tutorial <getting_started.html>`_.

.. code-block:: python

   root_dir = Path(r"")
   network_path = root_dir / "network"

   polygon = Polygon([
    [
        4.925796685034555,
        52.15567004009617
    ],
    [
        4.925796685034555,
        51.969875228118696
    ],
    [
        5.263478289905265,
        51.969875228118696
    ],
    [
        5.263478289905265,
        52.15567004009617
    ],
    [
        4.925796685034555,
        52.15567004009617
    ]
    ])

    # convert polygon into geojson file:
    gdf_polygon = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[polygon])
    gdf_polygon_path = network_path.joinpath("polygon.geojson")
    gdf_polygon.to_file(gdf_polygon_path, driver="GeoJSON")



Step 3. Network Configuration
-----------------------------


As a user, define the network configuration using the :class:`~ra2ce.network.network_config_data.network_config_data.NetworkConfigData` and
:class:`~ra2ce.network.network_config_data.network_config_data.NetworkSection` classes. Specify the source as :attr:`~ra2ce.network.network_config_data.enums.source_enum.SourceEnum.OSM_DOWNLOAD` to indicate that the network should be downloaded from OSM.
In this case, you also need to specify the road type to filter the roads to be included in the network. The available road types are defined in the :class:`~ra2ce.network.network_config_data.enums.road_type_enum.RoadTypeEnum` enumeration and follow the OSM classification.

.. code-block:: python

    network_section = NetworkSection(
    source=SourceEnum.OSM_DOWNLOAD,
    network_type=NetworkTypeEnum.DRIVE,
    road_types=[RoadTypeEnum.MOTORWAY, RoadTypeEnum.PRIMARY],
    polygon=gdf_polygon_path,
    save_gpkg=True,
    )

    network_config_data = NetworkConfigData(
    root_path=root_dir,
    static_path=root_dir / "static",
    network=network_section,
    )


Step 4. Initialize and Configure RA2CE
--------------------------------------
Running the :meth:`~ra2ce.ra2ce_handler.Ra2ceHandler.configure` method from the :meth:`~ra2ce.ra2ce_handler.Ra2ceHandler` will generate the network
and store the results in the ``static/output_graph`` folder.

.. code-block:: python

   handler = Ra2ceHandler.from_config(network=network_config_data, analysis=None)
   handler.configure()

Step 5. Load and Inspect the Output
-----------------------------------

A few geopackages are created in the ``static/output_graph`` folder, you can load and inspect them using ``geopandas``.

.. code-block:: python

   path_output_graph = root_dir.joinpath("static", "output_graph")
   base_graph_edges = path_output_graph.joinpath("base_graph_edges.gpkg")
   edges_gdf = gpd.read_file(base_graph_edges, driver="GPKG")

   base_graph_nodes = path_output_graph.joinpath("base_graph_nodes.gpkg")
   nodes_gdf = gpd.read_file(base_graph_nodes, driver="GPKG")


Step 6. Plot Nodes and Edges
----------------------------

.. code-block:: python

   fig, ax = plt.subplots(figsize=(15, 15))

   # Plot edges first
   baseplot = edges_gdf.plot(ax=ax, color="grey")

   # Overlay nodes
   nodes_gdf.plot(ax=baseplot, color="blue", markersize=20)

   plt.show()

.. image:: /_resources/figures/network_osm.png
   :alt: RA2CE OSM-based network
   :align: center
   :width: 80%