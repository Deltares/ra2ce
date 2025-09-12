Reference Damage Curves Tutorial
================================

This tutorial demonstrates how to run a **damage analysis using reference damage curves** in RA2CE.
Reference curves (such as the Huizinga et al. dataset) are widely used for rapid assessments of hazard-related damage,
as they provide generic hazard–damage relationships without requiring local calibration.

RA2CE provides several built-in options for vulnerability curves:

- **Global** → Huizinga curves (``HZ`` analysis name)
- **Europe** → OSDamage functions (``OSD`` analysis name)

These curves determine how hazard intensity (e.g., water depth) is translated into expected damage fractions.

.. note::

   - The **Huizinga curves** are the global default option and are widely used in international flood damage assessments. For more details, see publication by Huizinga et al. (2017): `Global flood depth-damage functions: Methodology and the database with guidelines <https://publications.jrc.ec.europa.eu/repository/handle/JRC105688>`_
   - The **OSDamage functions** provide Europe-specific depth–damage relations. For more details, see publication by van Ginkel et al. (2021): `Flood risk assessment of the European road network <https://nhess.copernicus.org/articles/21/1011/2021/>`_.

In this example, we will use **flood depth maps** as hazard input and apply the **Huizinga reference curves** to estimate
direct damages to road infrastructure.


----

Step 1: Define project paths
----------------------------

We first define the **root project folder** and its subdirectories:

.. code-block:: python

   from pathlib import Path

   root_dir = Path(r"c:\path\to\your\root_dir_ref_damage")

   static_path = root_dir.joinpath("static")
   hazard_path = static_path.joinpath("hazard")
   network_path = static_path.joinpath("network")
   output_path = root_dir.joinpath("output")

----

Step 2: Configure the road network and hazard
---------------------------------------------

The network is downloaded from **OpenStreetMap (OSM)**, clipped to a region polygon (``polygon.geojson``).
We specify which **road types** should be included in the analysis.

.. code-block:: python

   from ra2ce.network.network_config_data.enums.road_type_enum import RoadTypeEnum
   from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
   from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
   from ra2ce.network.network_config_data.network_config_data import NetworkSection

   network_section = NetworkSection(
       network_type=NetworkTypeEnum.DRIVE,
       source=SourceEnum.OSM_DOWNLOAD,
       polygon=static_path.joinpath("polygon.geojson"),
       save_gpkg=True,
       road_types=[
           RoadTypeEnum.SECONDARY,
           RoadTypeEnum.SECONDARY_LINK,
           RoadTypeEnum.PRIMARY,
           RoadTypeEnum.PRIMARY_LINK,
           RoadTypeEnum.TRUNK,
           RoadTypeEnum.MOTORWAY,
           RoadTypeEnum.MOTORWAY_LINK,
       ],
   )




We provide hazard input in the form of **GeoTIFF raster files** (e.g., flood depth maps).
RA2CE will overlay these rasters with the road network to compute hazard intensities for each asset.

.. code-block:: python

   from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
   from ra2ce.network.network_config_data.network_config_data import HazardSection

   hazard_section = HazardSection(
       hazard_map=[Path(file) for file in hazard_path.glob("*.tif")],
       aggregate_wl=AggregateWlEnum.MEAN,  # mean water depth used in analysis
       hazard_crs="EPSG:4326",  # ensure hazard map is in EPSG:4326 projection
   )


We combine the network and hazard information into a single configuration object.

.. code-block:: python

   from ra2ce.network.network_config_data.network_config_data import NetworkConfigData

   network_config_data = NetworkConfigData(
       root_path=root_dir,
       static_path=static_path,
       output_path=output_path,
       network=network_section,
       hazard=hazard_section
   )
   network_config_data.network.save_gpkg = True

----

Step 3: Define the damage analysis
----------------------------------

Here, we specify that RA2CE should perform a **damage analysis** using the
**Huizinga reference damage curves (HZ)** with the class :class:`~ra2ce.analysis.analysis_config_data.analysis_config_data.AnalysisSectionDamages` and its attribute :attr:`~ra2ce.analysis.analysis_config_data.enums.damage_curve_enum.DamageCurveEnum.HZ`.

.. code-block:: python

   from ra2ce.analysis.damages.damages import AnalysisSectionDamages
   from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import AnalysisDamagesEnum
   from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
   from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
   from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData

   damages_analysis = [AnalysisSectionDamages(
       name='damages_reference_curve_Huizinga',
       analysis=AnalysisDamagesEnum.DAMAGES,
       event_type=EventTypeEnum.EVENT,
       damage_curve=DamageCurveEnum.HZ,  # use Huizinga reference curve
       save_csv=True,
       save_gpkg=True
   )]

   analysis_config_data = AnalysisConfigData(
       analyses=damages_analysis,
       root_path=root_dir,
       output_path=output_path,
   )

----

Step 4: Run the analysis
------------------------

Finally, we run the analysis using the RA2CE handler.

.. code-block:: python

   from ra2ce.ra2ce_handler import Ra2ceHandler

   Ra2ceHandler.run_with_config_data(network_config_data, analysis_config_data)

----

Output
------

The results of the Huizinga damage analysis are provided in **two GeoPackage (GPKG) files**:

- **damages_reference_curve_Huizinga_link_based.gpkg**: damage estimates per **network link** (from node to node).
- **damages_reference_curve_Huizinga_segment.gpkg**: damage estimates per **segment** of 100m along the network.

Key attributes of interest in the output (expressed in currency) include:

- ``dam_EV1_HZ`` : estimated damage for the first flood map (Huizinga method).
- ``dam_EV2_HZ`` : estimated damage for the second flood map (Huizinga method).

You can open these files in GIS software (QGIS, ArcGIS) or load them in Python using GeoPandas for further analysis:

.. code-block:: python

   import geopandas as gpd
   output_path = root_dir / "output"
   link_based = gpd.read_file(output_path / "damages_reference_curve_Huizinga_link_based.gpkg")
   segment_based = gpd.read_file(output_path / "damages_reference_curve_Huizinga_segment.gpkg")

   # Inspect the first rows
   print(link_based.head())
   print(segment_based.head())

You can open the results in GIS software to visualize which road segments
are most affected by the hazard.

.. note::

   Reference damage curves provide **generalized estimates** of vulnerability.
   For more locally calibrated studies, consider using
   :doc:`manual damage curves <damages.manual_damage_curves>`.
