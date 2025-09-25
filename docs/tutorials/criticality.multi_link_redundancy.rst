Multi Link Redundancy
=====================

The multi-link redundancy analysis returns the same types of results as the single-link redundancy analysis, but it considers multiple links failing simultaneously. This is particularly useful for assessing the resilience of a network to natural disasters that may affect several links at once.

Run Multi-Link Redundancy Analysis
----------------------------------

The workflow is therefore very similar to the single-link redundancy analysis, with the difference being that a hazard map must be specified. See :doc:`criticality.single_link_redundancy` for more details on the workflow.

We select the analysis type as :attr:`~ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum.AnalysisLossesEnum.MULTI_LINK_REDUNDANCY` for which we can also set a threshold for the water depth. The threshold defines the hazard value above which a link is considered impassable/disrupted.

.. code-block:: python

   from pathlib import Path
   import geopandas as gpd
   from IPython.core.display_functions import display

   from ra2ce.analysis.analysis_config_data.analysis_config_data import AnalysisSectionLosses, AnalysisConfigData
   from ra2ce.analysis.analysis_config_data.enums.analysis_losses_enum import AnalysisLossesEnum
   from ra2ce.analysis.analysis_config_data.enums.weighing_enum import WeighingEnum
   from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
   from ra2ce.network.network_config_data.network_config_data import NetworkSection, NetworkConfigData, HazardSection
   from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
   from ra2ce.ra2ce_handler import Ra2ceHandler

   root_dir = Path(r'')

   network_path = root_dir / "network"
   hazard_path = root_dir / "hazard"

   network_section = NetworkSection(
       source=SourceEnum.SHAPEFILE,
       primary_file=[network_path.joinpath("base_shapefile.shp")],
       file_id="ID",
       save_gpkg=True)

   hazard_section = HazardSection(
       hazard_map=[hazard_path.joinpath("max_flood_depth.tif")],
       hazard_id='Flood',
       hazard_field_name="waterdepthtt",
       aggregate_wl=AggregateWlEnum.MIN,
       hazard_crs="EPSG:32736",
       )

   network_config_data = NetworkConfigData(
       root_path= root_dir,
       output_path=root_dir.joinpath("output"),
       static_path=root_dir.joinpath('static'),
       network=network_section,
       hazard=hazard_section,
       )

   analyse_section = AnalysisSectionLosses(
       name="tutorial_multi_link_redundancy",
       analysis=AnalysisLossesEnum.MULTI_LINK_REDUNDANCY,
       threshold=0.3,  # roads with a flood depth above this value are considered impassable
       weighing=WeighingEnum.LENGTH,
       save_csv=True,
       save_gpkg=True,
   )

   analysis_config_data = AnalysisConfigData(
       root_path=root_dir,
       output_path=root_dir.joinpath("output"),
       static_path=root_dir.joinpath('static'),
       analyses=[analyse_section],
       aggregate_wl=AggregateWlEnum.MIN,
   )

   handler = Ra2ceHandler.from_config(network=network_config_data, analysis=analysis_config_data)
   handler.configure()
   handler.run_analysis()


Inspect Results
---------------


.. code-block:: python

   analysis_output_folder = root_dir.joinpath("output", "multi_link_redundancy")
   redundancy_gdf = gpd.read_file(analysis_output_folder/"tutorial_multi_link_redundancy.gpkg") #specify the name of the geopackage holding your results (can be found in the analysis output folder)
   redundancy_gdf.head() #display the attributes of the file
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