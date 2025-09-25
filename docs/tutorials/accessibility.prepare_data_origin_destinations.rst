Origins and Destinations Data Preparation
=========================================

Before running any accessibility analysis in RA2CE, you must prepare two input
shapefiles:

- ``origins.shp`` → represents the **starting locations** (e.g. households, neighborhoods, schools).
- ``destinations.shp`` → represents the **end locations** (e.g. hospitals, shelters, workplaces).

Both files must follow a consistent structure so that RA2CE can correctly
recognize them and compute optimal routes.

----

Coordinate Reference System (CRS)
---------------------------------

Both shapefiles must:

- Be in a **projected coordinate system** (e.g preferably EPSG:4326).
- Use the **same CRS** for origins, destinations, and the network.

.. warning::

   If origins and destinations use a different CRS than the network,
   RA2CE will not run. Always check and reproject your data beforehand.

You can reproject your shapefiles using QGIS, ArcGIS, or GeoPandas:

.. code-block:: python

   import geopandas as gpd

   gdf = gpd.read_file("origins.shp")
   gdf = gdf.to_crs("EPSG:4326")
   gdf.to_file("origins_projected.shp")

----

Required Attributes
-------------------

Each shapefile must include specific attributes.

**Origins shapefile (origins.shp):**

- ``OBJECTID`` → unique identifier for each origin point.
- ``POPULATION`` → number of people represented at the origin
  (used to assess impact when access is lost).
- ``geometry`` → point geometry.

**Destinations shapefile (destinations.shp):**

- ``OBJECTID`` → unique identifier for each destination point.
- ``category`` *(optional)* → groups destinations by type, e.g.:

  - ``hospital``
  - ``school``
  - ``shelter``

- ``geometry`` → point geometry.



----

Creating Origins and Destinations
---------------------------------

There are several ways to create ``origins.shp`` and ``destinations.shp`` depending on your data.

Manual Preparation in QGIS
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can create the shapefiles manually in QGIS:

1. Open QGIS and create a **new point layer** (shapefile or GeoPackage).
2. Set the CRS to match your network (e.g. EPSG:4326).
3. Add the required fields:

   - ``OBJECTID`` (integer, unique)
   - ``POPULATION`` (integer, only for origins)
   - ``category`` (string, only for destinations)

4. Use the **Add Point Feature** tool to place points at the desired locations.
   - For origins: place them at households, neighborhood centroids, or village centers.
   - For destinations: place them at hospitals, schools, shelters, or other facilities.

5. Save the layer as ``origins.shp`` or ``destinations.shp``.


----

Generating Origins from OSM Buildings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of creating a grid or manually digitizing origins, you can also derive
them directly from **OpenStreetMap (OSM) building footprints**. This approach is
useful when:

- You want a realistic distribution of population across actual buildings.
- Census population totals are available, but not at building level.
- You prefer to avoid assumptions about evenly spaced origins (as in a grid).

The workflow is as follows:

1. Download building footprints from OSM within your study area polygon.
2. Compute the building footprint areas.
3. Redistribute the total population of your case study proportionally
   to the footprint area of each building.
4. Convert each building polygon into a representative point
   (for OD analysis).

Example Python script:

.. code-block:: python

   from pathlib import Path
   import osmnx
   import geopandas as gpd
   import numpy as np
   from shapely.geometry import shape

   # Define paths

   buffer_polygon_path = Path("buffer_polygon_OD.geojson")
   gdf = gpd.read_file(buffer_od)
   OD_polygon = shape(gdf.geometry.iloc[0])

   # Download OSM building footprints
   tags_basic_needs = {'building': ['yes']}
   features = osmnx.features_from_polygon(polygon=OD_polygon, tags=tags_basic_needs)

   # Assign IDs
   features['ID'] = range(len(features))
   origins = features[["ID", "building", "geometry"]]

   # Define total population for case study (to redistribute)
   population = {"Beira": 533825}
   case_study = "Beira"

   # Compute building areas (in projected CRS)
   crs = "EPSG:4326"   # example UTM zone, adjust for your area
   origins["Area"] = origins.to_crs(crs).geometry.area

   # Get total residential area to use as weight
   tot_res_area = np.sum(origins.loc[origins["building"] == "yes", "Area"])

   # Redistribute population proportionally to building footprint area
   people = []
   for i, row in origins.iterrows():
       if row["building"] == "yes":
           people.append(row["Area"] / tot_res_area * population[case_study])
       else:
           people.append(0)
   origins["POPULATION"] = people

   # Convert polygons to points (representative points inside buildings)
   origins["geometry"] = origins.geometry.apply(lambda geom: geom.representative_point())

   # Save as shapefile
   origins.to_file(network_path.joinpath("origins_OSM.shp"), driver="ESRI Shapefile")

This script generates an ``origins.shp`` file where:

- Each origin represents one **building** (represented as a point).
- The ``POPULATION`` attribute corresponds to the share of the total population
  allocated to that building.
- The total population in the shapefile matches the census total you defined.

.. note::

   - Adjust the CRS (``EPSG`` code) to your study area before computing areas.
   - The redistribution assumes that population is evenly distributed by
     building area, which is a simplification. If detailed population data
     is available, you should use it instead.



Generating Origins from WorldPop raster data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Work in Progress

Checklist
---------

✅ Both files use the same **projected CRS**
✅ ``OBJECTID`` present and unique
✅ ``POPULATION`` present in origins
✅ ``category`` optional in destinations
✅ Points fall **inside the study area polygon**

----

Next Steps
----------

Once your origins and destinations are ready, you can continue with one of the tutorials:

- :doc:`Defined Origin–Destination Pairs <accessibility.all_origin_destinations>`
- :doc:`Origins to Closest Destinations <accessibility.closest_origin_destinations>`
