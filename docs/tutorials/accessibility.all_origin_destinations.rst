Defined Origin–Destination Pairs Tutorial
=========================================

This tutorial demonstrates how to run a **Defined Origin–Destination (OD) analysis** with RA2CE.
In this mode, you explicitly provide a list of origins and destinations, and RA2CE calculates
the shortest or quickest routes between them.

This is useful when you already know the pairs of locations you want to analyze,
for example:

- From each residential area to a specific hospital
- From one school to a specific shelter
- From one town to another

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
   from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
   from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
   from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
   from ra2ce.network.network_config_data.network_config_data import (
       NetworkSection, NetworkConfigData, OriginsDestinationsSection, HazardSection, CleanupSection
   )
   from ra2ce.ra2ce_handler import Ra2ceHandler  # main handler for running RA2CE analyses

   # Specify the path to your RA2CE project folder and input data
   root_dir = Path(r"c:\path\to\your\root_dir_OD")

   network_path = root_dir.joinpath('static', 'network')

----

Step 2: Define network with Origins & Destinations
--------------------------

We define the network configuration, which in this example is downloaded from OpenStreetMap (OSM),
clipped to a region polygon. Only specific road types are included.

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

----


The OD analysis requires shapefiles for **origins** and **destinations**.
In this example, they are provided as ``origins.shp`` and ``destinations.shp``.

The class :class:`~ra2ce.network.network_config_data.network_config_data.OriginsDestinationsSection` is used to specify the paths to these shapefiles and
the shortcut names for the origin and destination points on the result files. The fields ``id_name_origin_destination`` and ``origin_count`` are mandatory and refer to attributes in the shapefiles.

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

We specify the analysis type as
:attr:`~ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum.AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_DESTINATION`.
This calculates optimal routes for the given OD pairs.

.. code-block:: python

   analyse_section = AnalysisSectionLosses(
       name="origin_destination_without_hazard",
       analysis=AnalysisLossesEnum.OPTIMAL_ROUTE_ORIGIN_DESTINATION,
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

Step 5: Inspect results
-----------------------

The results are stored in the ``output`` folder of your project directory.
They include both **CSV** and **GeoPackage (GPKG)** outputs with the routes
calculated for each defined OD pair, so the files contains as many routes as there are origin-destination pairs.

You can open the GPKG in GIS software or load it in Python with GeoPandas:

.. code-block:: python

   import geopandas as gpd

   results_gpkg = root_dir.joinpath("output", "optimal_route_origin_destination",  "origin_destination_without_hazard.gpkg"
   gdf = gpd.read_file(results_gpkg)
   gdf.head()

----

The image below shows for example all the shortest routes from a chosen origin (red circle) to all possible destinations (green starts).

.. image:: /_resources/Beira_OD_no_hazard.png
   :alt: Accessability of population to health centers in Sint Maarten under flood conditions
   :align: center
   :width: 100%