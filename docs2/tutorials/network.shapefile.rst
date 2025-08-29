Network from shapefile
======================


This tutorial shows how to create a road network from a shapefile using **RA2CE**.
You can use this workflow when you already have a geospatial dataset (instead of downloading from OpenStreetMap).



.. note::
   Make sure your shapefile contains valid road geometries (e.g. `LineString`) and that it’s projected in a suitable CRS (e.g. UTM). For more information on projections, see the `CRS documentation <https://proj.org/en/>`_.


Step 1. Import the Required Packages
------------------------------------

.. code-block:: python

   from pathlib import Path
   import geopandas as gpd
   import matplotlib.pyplot as plt

   from ra2ce.network.network_config_data.network_config_data import (
       NetworkSection, NetworkConfigData
   )
   from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
   from ra2ce.ra2ce_handler import Ra2ceHandler


Step 2. Define Paths and Network Configuration
----------------------------------------------

Indicate the path to the root directory of your project and to the network shapefile. We recommend to follow the structure shown in the `Getting Started tutorial <getting_started.html>`_.


As a user, define the network configuration using the :class:`~ra2ce.network.network_config_data.network_config_data.NetworkConfigData` and
:class:`~ra2ce.network.network_config_data.network_config_data.NetworkSection` classes.

.. code-block:: python

   root_dir = Path(r"")
   network_path = root_dir / "network"

   network_section = NetworkSection(
       source=SourceEnum.SHAPEFILE,
       primary_file=[network_path.joinpath("base_shapefile.shp")],
       file_id="ID",
       save_gpkg=True,
   )

   network_config_data = NetworkConfigData(
       root_path=root_dir,
       static_path=root_dir.joinpath("static"),
       network=network_section,
   )


Step 3. Initialize and Configure RA2CE
--------------------------------------
Running the :meth:`~ra2ce.ra2ce_handler.Ra2ceHandler.configure` method from the :meth:`~ra2ce.ra2ce_handler.Ra2ceHandler` will generate the network
and store the results in the ``static/output_graph`` folder.

.. code-block:: python

   handler = Ra2ceHandler.from_config(network=network_config_data, analysis=None)
   handler.configure()



Step 4. Load and Inspect the Output
-----------------------------------

A few geopackages are created in the ``static/output_graph`` folder, you can load and inspect them using ``geopandas``.
.. code-block:: python

   path_output_graph = root_dir / "static" / "output_graph"
   base_graph_edges = path_output_graph / "base_graph_edges.gpkg"
   edges_gdf = gpd.read_file(base_graph_edges, driver="GPKG")

   base_graph_nodes = path_output_graph / "base_graph_nodes.gpkg"
   nodes_gdf = gpd.read_file(base_graph_nodes, driver="GPKG")


Step 5. Plot Nodes and Edges
----------------------------

.. code-block:: python

   fig, ax = plt.subplots(figsize=(15, 15))

   # Plot edges first
   baseplot = edges_gdf.plot(ax=ax, color="grey")

   # Overlay nodes
   nodes_gdf.plot(ax=baseplot, color="blue", markersize=20)

   plt.show()

.. image:: /_resources/figures/network_shapefile.png
   :alt: RA2CE shapefile-based network
   :align: center
   :width: 80%