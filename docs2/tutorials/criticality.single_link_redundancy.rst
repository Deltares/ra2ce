Single Link Redundancy Tutorial
===============================

🚗 What happens if one road is blocked?
--------------------------------------

In this tutorial, you will learn how to run a **single link redundancy analysis**
with RA2CE. This type of analysis checks what happens if *one road segment*
(also called a *link*) becomes unavailable:

- Is there another way to get around?
- How much longer is the detour compared to the original route?
- Which roads have **no backup options at all**?

.. note::

   This example does **not** require hazard maps, but you do need a prepared network.
   If you are new to networks in RA2CE, first go through the :doc:`network` tutorial.

.. image:: /_resources/criticality_schema.png
   :alt: Basic principle of the single link redundancy analysis
   :align: center
   :width: 80%

The redundancy of each link is expressed in the total distance (weighing) for the alternative route (weighing = distance).
Below is a complete Python example demonstrating how to run a single link redundancy analysis with RA2CE.

Step 1: Import Libraries and Set Paths
--------------------------------------

We start by importing the required libraries and defining the root directory and network path.

.. code-block:: python

   from pathlib import Path
   import geopandas as gpd

   from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionLosses, AnalysisConfigData
   from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import AnalysisLossesEnum
   from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
   from ra2ce.network.network_config_data.network_config_data import NetworkSection, NetworkConfigData
   from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
   from ra2ce.ra2ce_handler import Ra2ceHandler

   root_dir = Path(r'')
   network_path = root_dir / "network"



Step 2: Define Network and Analysis Configuration
-------------------------------------------------


.. code-block:: python

   # Define the network section
   network_section = NetworkSection(
       source=SourceEnum.SHAPEFILE,
       primary_file=[network_path.joinpath("base_shapefile.shp")],
       file_id="ID",
       save_gpkg=True
   )

   # Build the full configuration
   network_config_data = NetworkConfigData(
       root_path=root_dir,
       static_path=root_dir.joinpath('static'),
       output_path=root_dir.joinpath('static/output_graph'),
       network=network_section,
   )

Next, we define the :class:`~ra2ce.analysis.analysis_config_data.analysis_config_data.AnalysisSectionLosses` and :class:`~ra2ce.analysis.analysis_config_data.analysis_config_data.AnalysisConfigData` sections of the configuration. We select the analysis type as :attr:`~ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum.AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY` and the weighing method as :attr:`~ra2ce.analysis.analysis_config_data.enums.weighing_enum.WeighingEnum.LENGTH`. We also specify that we want to save the results in both CSV and GPKG formats.


.. code-block:: python

   analyse_section = AnalysisSectionLosses(
       name="tutorial_single_link_redundancy",
       analysis=AnalysisLossesEnum.SINGLE_LINK_REDUNDANCY,
       weighing=WeighingEnum.LENGTH,
       save_csv=True,
       save_gpkg=True,
   )

   analysis_config_data = AnalysisConfigData(
       root_path=root_dir,
       output_path=root_dir.joinpath("output"),
       static_path=root_dir.joinpath('static'),
       analyses=[analyse_section],
   )



Running the :meth:`~ra2ce.ra2ce_handler.Ra2ceHandler.configure` method from the :meth:`~ra2ce.ra2ce_handler.Ra2ceHandler` will generate both the base network and the overlaid network, and will store these results in the ``static/output_graph`` folder.

.. code-block:: python

   handler = Ra2ceHandler.from_config(network=network_config_data, analysis=analysis_config_data)
   handler.configure()
   handler.run_analysis()



Step 3: Inspect results
-----------------------

The results are stored in the folder ``output`` within the root directory. The results include a CSV file and a GPKG file containing the redundancy analysis results for each link in the network.

.. code-block:: python

   analysis_output_folder = root_dir.joinpath("output", "single_link_redundancy")
   redundancy_gdf = gpd.read_file(analysis_output_folder/"tutorial_single_link_redundancy.gpkg") #specify the name of the geopackage holding your results (can be found in the analysis output folder)
   redundancy_gdf.head() #display the attributes of the file


Detour Availability
~~~~~~~~~~~~~~~~~~~

RA2CE marks whether each road segment has a detour:

- ``0`` = no detour available (critical!)
- ``1`` = detour available

This is stored in the ``detour`` column.

.. code-block:: python

   import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 10))
    redundancy_gdf.plot(column='detour', ax=ax, legend=False, cmap='viridis')
    # `output_path` specified in the `NetworkConfigData` and `AnalysisConfigData`.
    plt.title('Single Link Redundancy Analysis Results')
    # `output_path` specified in the `NetworkConfigData` and `AnalysisConfigData`.
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True)
    plt.show()

.. image:: /_resources/figures/criticality_detour.png
   :alt: Criticality results: detour attribute, yellow (1) = detour available, purple (0) = no detour available
   :align: center
   :width: 80%


Alternative route distance
~~~~~~~~~~~~~~~~~~~~~~~~~~

We can now check the lengths of the alternative distance for each link in the network with the attribute ‘alt_dist’. The alternative distance refers to the length of the detour for when the link itself is not available.


.. code-block:: python

   import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 10))
    redundancy_gdf.plot(column='alt_length', ax=ax, legend=False, cmap='viridis')
    # `output_path` specified in the `NetworkConfigData` and `AnalysisConfigData`.
    plt.title('Single Link Redundancy Analysis Results')
    # `output_path` specified in the `NetworkConfigData` and `AnalysisConfigData`.
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True)
    plt.show()

.. image:: /_resources/figures/criticality_alt_length.png
   :alt: Criticality results: alternative distance in meters.
   :align: center
   :width: 80%


It should be noted that are cases where the original distance can be longer than the alternative distance. In the example below, from A (818) to B (828) the alternative distance between nodes 818 and 828 (road 1621) is shorter than the length of road nr. 1622. Therefore, the ‘diff_dist’ attribute contains a negative value. The original link is longer than the alternative route! This is purely relevant from a network inspection point of view. In reality, most people will take road 1621 to get from A to B (if that road segment is available).

.. image:: /_resources/criticality_neg.png
   :align: center
   :width: 80%

