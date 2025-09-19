Expected Annual Damage (EAD) Tutorial
=====================================

This tutorial demonstrates how to run a **risk-based damage analysis** in RA2CE,
calculating the **Expected Annual Damage (EAD)** to road infrastructures.

Unlike the event-based analysis (where damages are computed for a single hazard event),
the EAD approach integrates damages across multiple hazard scenarios with different
return period. This provides a long-term measure of *average annual risk*.

----

What is EAD?
------------

The **Expected Annual Damage (EAD)** represents the average yearly damage that can
be expected due to hazards, accounting for their frequency of occurrence.

The workflow follows the same steps as the event-based analysis, with the key
difference being:

- **Hazard input** consists of maps corresponding to different return periods
  (e.g., 10-year, 100-year, 1000-year floods).
- RA2CE combines the **damage per event** with the **annual exceedance probability (AEP)**
  of each event.
- Damages are integrated across probabilities to estimate the **EAD**.

----

This tutorial is mostly based on the tutorial about reference damage curves. For details on
the road network setup and hazard input, please refer to the :doc:`Reference Damage Curves Tutorial <damages.reference_damage_curves>`.

Step 1: Define project paths
----------------------------

We first set up the project folder structure:

.. code-block:: python

   from pathlib import Path

   root_dir = Path(r"c:\path\to\your\root_dir_ref_damage_risk")
   assert root_dir.exists(), "root_dir not found."

   static_path = root_dir.joinpath("static")
   hazard_path = static_path.joinpath("hazard")
   network_path = static_path.joinpath("network")
   output_path = root_dir.joinpath("output")

----

Step 2: Configure the road network
----------------------------------

The road network is downloaded from **OpenStreetMap (OSM)** and clipped to
a region polygon (``polygon.geojson``). We select which road types should be
included in the analysis.

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

----


Hazard maps are provided as **GeoTIFF raster files** for different return periods
(e.g., 10-year, 100-year, 1000-year). RA2CE will use these to compute damages
for each event.

.. warning::
   Hazard maps must follow the naming convention ``RP_<return_period>.tif``
   (e.g. ``RP_10.tif``, ``RP_100.tif``, ``RP_1000.tif``).
   Otherwise, RA2CE will not be able to assign exceedance probabilities.


.. code-block:: python

   from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
   from ra2ce.network.network_config_data.network_config_data import HazardSection

   hazard_section = HazardSection(
       hazard_map=[Path(file) for file in hazard_path.glob("*.tif")],
       aggregate_wl=AggregateWlEnum.MEAN,
       hazard_crs="EPSG:4326",
   )

----


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

We now configure the analysis to compute **risk-based damages** with the analysis section class
:class:`~ra2ce.analysis.damages.damages.AnalysisSectionDamages`.
The Expected Annual Damage (EAD) is calculated by integrating damages across multiple return periods —
this is essentially the area under the Exceedance Probability (EP) curve.

For a risk analysis, two additional attributes must be specified:

- ``risk_calculation_mode`` → defines how the area under the EP curve is approximated.
  Available options are provided by
  :class:`~ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum.RiskCalculationModeEnum`.
- ``risk_calculation_year`` → only required for the **Triangle to Null Year** mode.
  It specifies a synthetic minimum return period (in years) at which damages are assumed to be zero.
  This extends the EP curve towards the y-axis and ensures integration includes frequent (low-return period) events.

RA2CE allows for several modes of calculating the EAD.
In this tutorial, we use the **Triangle to Null Year** method, which linearly approximates the
area under the EP curve from the lowest available hazard map down to the defined ``risk_calculation_year``.


.. image:: /_resources/triangle_to_null.png
   :alt:
   :align: center
   :width: 100%

In this example, we set ``risk_calculation_year=5`` to include frequent events
with return periods down to 5 years in the EAD computation.

.. code-block:: python

   from ra2ce.analysis.damages.damages import AnalysisSectionDamages
   from ra2ce.analysis.analysis_config_data.enums.analysis_damages_enum import AnalysisDamagesEnum
   from ra2ce.analysis.analysis_config_data.enums.event_type_enum import EventTypeEnum
   from ra2ce.analysis.analysis_config_data.enums.damage_curve_enum import DamageCurveEnum
   from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisConfigData
   from ra2ce.analysis.analysis_config_data.enums.risk_calculation_mode_enum import RiskCalculationModeEnum


   damages_analysis = [AnalysisSectionDamages(
       name='damages_risk',
       analysis=AnalysisDamagesEnum.DAMAGES,
       event_type=EventTypeEnum.RETURN_PERIOD,  # risk-based analysis
       damage_curve=DamageCurveEnum.HZ,         # use Huizinga reference curves
       risk_calculation_mode=RiskCalculationModeEnum.TRIANGLE_TO_NULL_YEAR,
       risk_calculation_year=5,                 # include frequent events
       save_csv=True,
       save_gpkg=True,
   )]

   analysis_config_data = AnalysisConfigData(
       analyses=damages_analysis,
       root_path=root_dir,
       output_path=output_path,
   )


Step 4: Run the analysis
------------------------

Finally, we run the analysis:

.. code-block:: python

   from ra2ce.ra2ce_handler import Ra2ceHandler

   Ra2ceHandler.run_with_config_data(network_config_data, analysis_config_data)

----

Output
------

The results are written to **GeoPackage (GPKG)** and CSV files in the ``output`` folder.

Typical outputs include:

- **damages_risk_link_based.gpkg** – damages per network link (node to node).
- **damages_risk_segment.gpkg** – damages per 100m segment.

Attributes of interest include:

- ``dam_RP100_HZ`` – estimated damage for the 100-year return period (Huizinga).
- ``dam_RP1000_HZ`` – estimated damage for the 1000-year return period (Huizinga).
- ``risk_HZ`` – Expected Annual Damage, aggregated across return periods.

You can load the results with **GeoPandas** for inspection and plotting:

.. code-block:: python

   import geopandas as gpd

   link_based = gpd.read_file(output_path / "damages_risk_link_based.gpkg")
   print(link_based[["dam_RP100_HZ", "dam_RP1000_HZ", "risk_HZ"]].head())

----

.. note::

   The accuracy of the EAD strongly depends on the **set of return period hazard maps** provided.
   Ensure that you cover a sufficient range (e.g., frequent, moderate, and extreme events)
   to avoid underestimating or overestimating the risk.
