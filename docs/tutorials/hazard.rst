Hazard
======

In this tutorial, we will guide you through performing a hazard overlay with a network using RA2CE.
This tutorial assumes you already have a road network.
If not, please first visit the :doc:`Network tutorial <network>`.

Hazard Map
----------

To overlay a hazard map with a road network, you will need a hazard map file.
RA2CE supports hazard maps in raster format (e.g., GeoTIFF).

A hazard map is geospatial data representing the extent and severity of a hazard in a specific area.
It is typically stored as a grid of cells, where each cell contains a value indicating the hazard intensity at that location.

.. note::

   RA2CE is **hazard agnostic**: it does not depend on the type of hazard.
   Any hazard that can be represented in a raster format (flood, landslide, wildfire) can be used.


What is hazard overlay?
-----------------------

The principle of a hazard overlay is straightforward: the road network is represented as a set of links and nodes,
while the hazard map is a raster grid of intensity values.
By spatially overlaying the network onto the hazard map, each road segment is assigned the hazard values of the
cells it intersects. This allows RA2CE to quantify the level of exposure of the network to the given hazard,
and provides the basis for further analysis such as risk assessment or accessibility studies.


Hazard overlay in RA2CE
-----------------------

For this tutorial, we will use a sample flood hazard map in Beira (Mozambique) that shows the water depth at each location.
We start with imports and defining relevant paths:


.. code-block:: python

   from pathlib import Path
   import geopandas as gpd

   from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
   from ra2ce.network.network_config_data.network_config_data import (
       NetworkSection, NetworkConfigData, HazardSection
   )
   from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
   from ra2ce.ra2ce_handler import Ra2ceHandler

   # Root project directory
   root_dir = Path(r'c:\Users\username\Documents\RA2CE_tutorial\root_dir')

   network_path = root_dir / "network"
   hazard_path = root_dir / "hazard"


Next, we define the :class:`~ra2ce.network.network_config_data.network_config_data.NetworkSection` and :class:`~ra2ce.network.network_config_data.network_config_data.HazardSection` sections of the configuration.
As a user, you need to specify the CRS projection of the hazard map using the ``hazard_crs`` parameter. If the projection of the hazard map does not match the one of the network, RA2CE will try to reproject. However, it is recommended to provide hazard maps in the same projection as the network to avoid potential reprojection issues in EPSG 4326 system (default).
An aggregation method must also be specified using the ``aggregate_wl`` parameter from the :class:`~ra2ce.network.network_config_data.enums.aggregate_wl_enum.AggregateWlEnum` enumeration.

.. code-block:: python

   # Define the network section
   network_section = NetworkSection(
       source=SourceEnum.SHAPEFILE,
       primary_file=[network_path.joinpath("base_shapefile.shp")],
       file_id="ID",
       save_gpkg=True
   )

   # Define the hazard section
   hazard_section = HazardSection(
       hazard_map=[hazard_path.joinpath("max_flood_depth.tif")],
       aggregate_wl=AggregateWlEnum.MEAN,
       hazard_crs="EPSG:32736",
   )

   # Build the full configuration
   network_config_data = NetworkConfigData(
       root_path=root_dir,
       static_path=root_dir.joinpath('static'),
       output_path=root_dir.joinpath('static/output_graph'),
       network=network_section,
       hazard=hazard_section
   )




Running the :meth:`~ra2ce.ra2ce_handler.Ra2ceHandler.configure` method from the :meth:`~ra2ce.ra2ce_handler.Ra2ceHandler` will generate both the base network and the overlaid network, and will store these results in the ``static/output_graph`` folder.

.. code-block:: python

   handler = Ra2ceHandler.from_config(network=network_config_data, analysis=None)
   handler.configure()


.. code-block:: console

   100%|██████████| 4217/4217 [00:00<00:00, 421640.09it/s]
   2025-08-29 11:55:01 AM - [avg_speed_calculator.py:176] - root - WARNING - No valid file found with average speeds c:\Users\hauth\OneDrive - Stichting Deltares\Documents\tempo\RA2CE_docu\root_dir\static\output_graph\avg_speed.csv, calculating and saving them instead.
   2025-08-29 11:55:01 AM - [avg_speed_calculator.py:151] - root - WARNING - Default speed have been assigned to road type [<RoadTypeEnum.SECONDARY_LINK: 8>]. Please check the average speed CSV, enter the right average speed for this road type and run RA2CE again.
   2025-08-29 11:55:01 AM - [avg_speed_calculator.py:151] - root - WARNING - Default speed have been assigned to road type [<RoadTypeEnum.SECONDARY: 7>]. Please check the average speed CSV, enter the right average speed for this road type and run RA2CE again.
   2025-08-29 11:55:04 AM - [hazard_overlay.py:381] - root - WARNING - Hazard crs EPSG:32736 and graph crs EPSG:4326 are inconsistent, we try to reproject the graph crs
   Graph hazard overlay with max_flood_depth: 100%|██████████| 2109/2109 [00:15<00:00, 138.86it/s]
   Graph fraction with hazard overlay with max_flood_depth: 100%|██████████| 2109/2109 [00:43<00:00, 48.49it/s]
   2025-08-29 11:56:04 AM - [hazard_overlay.py:462] - root - WARNING - Hazard crs EPSG:32736 and gdf crs EPSG:4326 are inconsistent, we try to reproject the gdf crs
   2025-08-29 11:56:04 AM - [hazard_intersect_builder_for_tif.py:179] - root - WARNING - Some geometries have NoneType objects (no coordinate information), namely: Empty GeoDataFrame
   Columns: [link_id, ID, highway, avgspeed, geometry, lanes, length, maxspeed, bridge, node_A, node_B, edge_fid, rfid_c, rfid, time]
   Index: [].This could be due to segmentation, and might cause an exception in hazard overlay
   Network hazard overlay with max_flood_depth: 100%|██████████| 2121/2121 [00:16<00:00, 126.84it/s]
   Network fraction with hazard overlay with max_flood_depth: 100%|██████████| 2121/2121 [00:38<00:00, 55.74it/s]



Results
-------

Once you have run a RA2CE analysis performing a hazard overlay, the results can be found in the
``output_graph`` folder. Files containing ``*_hazard`` hold the results of the overlay with the hazard.

Notice the attribute ``EV1_ma`` from the file base_network_hazard.gpkg. This attribute represents the hazard value for each road segment:

- ``EV1`` stands for **Event 1**. If you run multiple hazard maps, subsequent columns will be called
  ``EV2``, ``EV3``, etc.
- ``_ma`` refers to **maximum flood depth**, which corresponds to the parameter specified in the
  ``HazardSection``.

When performing RA2CE analyses with flooding and a road network, it is common to use the maximum water depth
for each segment. This is because a vehicle can only traverse a road segment if it can drive through the
largest water depth present on that segment.

.. note::

   If there is an existing ``base_graph`` in the ``output_graph`` folder, RA2CE will always use this graph.
   If you need to update or regenerate the graph, you must manually remove the existing ``base_graph``
   from the folder before rerunning the analysis.

.. code-block:: python

   hazard_output = root_dir / "static" / "output_graph" / "base_graph_hazard_edges.gpkg"
   hazard_gdf = gpd.read_file(hazard_output, driver = "GPKG")
   hazard_gdf.head()