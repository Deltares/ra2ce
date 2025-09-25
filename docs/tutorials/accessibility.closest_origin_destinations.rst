Origins to Closest Destinations Tutorial
=========================================

This tutorial demonstrates how to run an **Origins to Closest Destinations (OD) analysis** with RA2CE.
In this mode, RA2CE automatically finds the shortest or quickest route from each origin to its **nearest destination**.

This is especially useful when you want to evaluate accessibility to services without having to define explicit OD pairs.
For example:

- From every household to the closest hospital
- From every school to the nearest shelter
- From each neighborhood to the nearest service facility (hospital, school, shelter, etc.)

If you are not yet familiar with how to prepare the origins and destinations shapefiles,
please first go through the :doc:`Origins and Destinations data preparation <accessability.prepare_data_origin_destionations>` tutorial.

----

Step 1: Import libraries and set paths
--------------------------------------

We start by importing the required libraries and defining the root directory
that contains the input data.

.. code-block:: python

   from pathlib import Path

   from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionLosses, AnalysisConfigData
   from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import AnalysisLossesEnum
   from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
   from ra2ce.network import RoadTypeEnum
   from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
   from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
   from ra2ce.network.network_config_data.network_config_data import (
       NetworkSection, NetworkConfigData, OriginsDestinationsSection
   )
   from ra2ce.ra2ce_handler import Ra2ceHandler  # main handler for running RA2CE analyses

   # Specify the path to your RA2CE project folder and input data
   root_dir = Path(r"c:\path\to\your\root_dir_OD")

   network_path = root_dir.joinpath('static', 'network')

----

Step 2: Define network with Origins & Destinations
--------------------------------------------------

The network is defined using OSM data clipped to a region polygon,
with selected road types.

.. code-block:: python

   network_section = NetworkSection(
       source=SourceEnum.OSM_DOWNLOAD,
       polygon=network_path.joinpath("region_polygon.geojson"),
       network_type=NetworkTypeEnum.DRIVE,
       road_types=[
           RoadTypeEnum.MOTORWAY,
           RoadTypeEnum.MOTORWAY_LINK,
           RoadTypeEnum.PRIMARY,
           RoadTypeEnum.PRIMARY_LINK,
           RoadTypeEnum.SECONDARY,
           RoadTypeEnum.SECONDARY_LINK,
           RoadTypeEnum.TERTIARY,
           RoadTypeEnum.TERTIARY_LINK,
           RoadTypeEnum.RESIDENTIAL,
       ],
       file_id="rfid_c",
       save_gpkg=True
   )

The OD analysis requires shapefiles for **origins** and **destinations**.
In this case, destinations can also be grouped into **categories** (e.g. hospitals, schools, shelters).
RA2CE will then find the nearest destination for each origin **per category** if specified. in the class
:attr:`~ra2ce.network.network_config_data.network_config_data.OriginsDestinationsSection`.

.. code-block:: python

   origin_destination_section = OriginsDestinationsSection(
       origins=network_path.joinpath("origins.shp"),
       destinations=network_path.joinpath("destinations.shp"),
       origins_names="A",
       destinations_names="B",
       id_name_origin_destination="OBJECTID",
       origin_count="POPULATION",
   )

Now we combine the network and origin–destination information.

.. code-block:: python

   network_config_data = NetworkConfigData(
       root_path=root_dir,
       output_path=root_dir.joinpath("output"),
       static_path=root_dir.joinpath('static'),
       network=network_section,
       origins_destinations=origin_destination_section,
   )

----

Step 3: Define the analysis
---------------------------

- If you want to find the closest route in **normal conditions** (no hazard disruption),
  use :attr:`~ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum.AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_CLOSEST_DESTINATION`.

- If you want to account for **hazard disruption** (e.g. flooded roads),
  use :attr:`~ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum.AnalysisLossesEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION`.

In this example, we use the latter, which allows for calculating routes that avoid disrupted roads.

.. code-block:: python

   analyse_section = AnalysisSectionLosses(
       name="OD_accessibility_analysis",
       analysis=AnalysisLossesEnum.MULTI_LINK_ORIGIN_CLOSEST_DESTINATION,
       weighing=WeighingEnum.LENGTH,
       calculate_route_without_disruption=True,
       save_csv=True,
       save_gpkg=True,
   )

   analysis_config_data = AnalysisConfigData(
       root_path=root_dir,
       output_path=root_dir.joinpath("output"),
       static_path=root_dir.joinpath('static'),
       analyses=[analyse_section],
   )

----

Step 4: Run the analysis
------------------------

We use the :class:`~ra2ce.ra2ce_handler.Ra2ceHandler` to configure and run the analysis.

.. code-block:: python

   handler = Ra2ceHandler.from_config(
       network=network_config_data,
       analysis=analysis_config_data
   )
   handler.configure()
   handler.run_analysis()

----

Step 5: Interpret Results
-------------------------

Once the analysis has been completed, RA2CE produces outputs in the ``output`` folder of your project directory.
These include both **CSV** and **GeoPackage (GPKG)** files, which you can open in GIS software or in Python
(for example with GeoPandas).

.. code-block:: python

   import geopandas as gpd

   analysis_output_path = root_dir / "output" / "OD_accessibility_analysis"
   results_gpkg = analysis_output_path / "OD_accessibility_analysis_optimal_routes_without_hazard.gpkg"

   gdf = gpd.read_file(results_gpkg)
   gdf.head()

.. note::

   The ``.explore()`` method applied to GeoDataFrame is used in this tutorial and works best in Jupyter notebooks.
   If you are running RA2CE in a plain Python script, you can instead:

   - Save results to GeoPackage and open them in QGIS/ArcGIS
   - Use ``folium`` to export interactive maps to HTML
   - Use ``matplotlib`` for static plots

The following sub-sections demonstrate different ways to explore and interpret these results.

----

Identifying isolated populations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is interesting to inspect which origins (e.g. population centers) have lost access to their closest destination because of hazard disruption.
The file ``OD_accessibility_analysis_origins.gpkg`` contains an attribute ``EV1_me_A`` that indicates if an origin has access to its closest destination or not.

- ``access`` → reachable destination exists
- ``no access`` → origin is cut off

.. code-block:: python

   origin_gdf = gpd.read_file(analysis_output_path / 'OD_accessibility_analysis_origins.gpkg')
   map = origin_gdf.explore(column='EV1_me_A', cmap=['green', 'red'],
                            marker_kwds={'radius':5}, tiles="CartoDB dark_matter")
   map.save("access_POP.html")

.. image:: /_resources/Beira_access_pop.png
   :alt: Comparison of optimal routes before and after hazard
   :align: center
   :width: 100%

You can also inspect how many people are affected by lack of access by filtering the origins that have ``no access`` and visualizing them with the ``POPULATION`` attribute.

.. code-block:: python

   no_access_gdf = origin_gdf[origin_gdf['EV1_me_A'] == 'no access']
   no_access_gdf.explore(column='POPULATION', cmap='cool',
                         marker_kwds={'radius':5}, tiles="CartoDB dark_matter")

----

Inspecting optimal routes
~~~~~~~~~~~~~~~~~~~~~~~~~

RA2CE computes **optimal routes** from each origin to its closest destination (or per category if defined).
For every origin that still has access, RA2CE provides a route that can be visualized and further analyzed.
The file ``OD_accessibility_analysis_optimal_routes_with_hazard.gpkg`` represents these routes.


If you want to focus on a single destination, for example ``B_6``, you can filter the dataset:

.. code-block:: python

   destinations_gdf = gpd.read_file(analysis_output_path / 'OD_accessibility_analysis_destinations.gpkg')
   optimal_routes_with_hazard_gdf = gpd.read_file(analysis_output_path / 'OD_accessibility_analysis_optimal_routes_with_hazard.gpkg')

   b_6_gdf = destinations_gdf[destinations_gdf['d_id'] == 'B_6']
   optimal_routes_b_6_with_hazard_gdf = optimal_routes_with_hazard_gdf[optimal_routes_with_hazard_gdf['destination'] == 'B_6']
   origins_with_optimal_route_b_6 = origin_gdf[origin_gdf['o_id'].isin(optimal_routes_b_6_with_hazard_gdf['origin'])]

   optimal_routes_b_6_with_hazard_gdf.explore(column='difference',
                                              cmap='RdYlGn_r', legend=True,
                                              tiles="CartoDB dark_matter")

In this map, routes are colored by the **difference in travel time or distance** between the baseline and hazard scenario.

.. image:: /_resources/Beira_OD_closest.png
   :alt: Comparison of optimal routes before and after hazard
   :align: center
   :width: 100%

It is convenient to use QGIS to inspect the results further and create custom maps. We see for example below the different
clusters of origins that are connected to the same closest destination.

.. image:: /_resources/Beira_OD_closest2.png
   :alt: Comparison of optimal routes before and after hazard
   :align: center
   :width: 100%

**Key differences between before and after hazard:**

- Some routes may no longer exist if disrupted roads block all access
- Remaining routes may be longer or slower, showing detours
- Some origins may completely lose access to the destination

This comparison allows you to quantify **loss of accessibility** in the aftermath of natural hazard.

----

When to use this analysis
-------------------------

Choose the **Origins to Closest Destinations analysis** when:

- You want to identify nearest essential services for households or neighborhoods
- You are planning evacuation routes to the nearest shelter in case of a hazard
- You need to evaluate service accessibility across multiple destination categories

.. note::

   In some cases, origins may become **isolated** due to hazard disruption (e.g. flooded or blocked roads).
   In such cases, no valid route to any destination can be found.
   These isolated origins are flagged in the results and should be carefully considered
   in emergency planning and recovery strategies.
