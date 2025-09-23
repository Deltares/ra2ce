Getting Started
===============

This section will help you get up and running quickly with **RA2CE**.
It covers installation, key concepts, and a short example to start using the library right away.

.. contents::
   :local:
   :depth: 1


Introduction
------------

This is the repository of **RA2CE** (*just say race!*) — the *Resilience Assessment and Adaptation for Critical
infrastructurE* Toolkit Python package developed by Deltares.

RA2CE helps to:

- Quantify resilience of critical infrastructure networks
- Prioritize interventions and adaptation measures
- Set up emergency response plans related to critical infrastructure


Installation
------------

You can install **RA2CE** with pip:

.. code-block:: bash

   pip install ra2ce

Alternatively, you can install the latest version available on GitHub,
or a specific tag / commit hash using the ``@`` symbol:

.. code-block:: bash

   pip install git+https://github.com/Deltares/ra2ce.git
   pip install git+https://github.com/Deltares/ra2ce.git@v1.0.0


Developer Mode
~~~~~~~~~~~~~~

To install RA2CE for development purposes, please refer to our
`installation for contributors wiki page <https://github.com/Deltares/ra2ce/wiki/getting-started#installation-for-contributors>`_.


Fundamentals
------------

How to Run Python (Sandbox, Jupyter, Binder, Docker)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use **RA2CE** in several ways:

- **Python script (sandboxing)**: write and run scripts that call RA2CE functions.
- **Jupyter Notebook**: recommended for interactive exploration and visualization.

Example:

.. code-block:: python

   import ra2ce

**Binder** provides an online environment with RA2CE pre-installed.
It includes ready-to-run examples, and lets you create your own notebooks or experiment with the CLI.

- Try our `RA2CE Binder environment <https://mybinder.org/v2/gh/Deltares/ra2ce/jupyter-binder>`_
- Learn more about `Binder <https://mybinder.readthedocs.io/en/latest/>`_

You can also use **Docker** to install RA2CE and run it on different cloud services.
See our `Docker and cloud wiki page <https://github.com/Deltares/ra2ce/wiki/Docker-and-Cloud>`_ for instructions.


GIS Basics: Projection, Raster, Shapefiles, QGIS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**RA2CE** heavily relies on geospatial data.
Familiarity with GIS tools is recommended for effective use.

RA2CE generates and processes both **raster** and **vector** data.
Most outputs are written to the `.gpkg` format, which can be opened in **QGIS** — a free, open-source GIS application.
QGIS is especially useful for:

- Pre-processing input data
- Reprojecting layers into a consistent CRS
- Visualizing results after running analyses

.. important::

   All GIS datasets must use the same **Coordinate Reference System (CRS)**.
   We recommend reprojecting to **EPSG:4326 (WGS84)** for maximum compatibility.
   Within Python, you can use libraries such as `pyproj`, `rasterio`, and `geopandas`.

Key formats:

- **Raster files**: continuous data (e.g., elevation, hazard intensity)
- **Shapefiles / GeoPackage**: vector data (points, lines, polygons)


Folder Structure
~~~~~~~~~~~~~~~~

RA2CE can be run from any location, but it expects a **consistent project folder structure**.
Each project folder must contain:

- ``output/`` — results from analyses
- ``static/`` — input data that does not change between runs
  - ``hazard/``: hazard datasets (rasters)
  - ``network/``: network datasets (e.g., OSM PBF or GeoJSON)
  - ``output_graph/``: intermediate graphs, useful for quality control

Example structure:

.. code-block:: text

   ProjectA/
   ├── output/              # Contains analysis results
   ├── static/              # Static input data
   │   ├── hazard/          # Hazard datasets
   │   ├── network/         # Network data
   │   └── output_graph/    # Intermediate network files


Workflow: Define a Network and Run an Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The general workflow in RA2CE follows four steps:

1. **Prepare data**: organize GIS datasets in the required folder structure.
2. **Define the network**: load and preprocess network data.
3. **Run analysis**: perform simulations such as connectivity or hazard impact analysis.
4. **Visualize results**: inspect outputs in QGIS or process them further in Python.

(Example code snippet can be added here once you decide on the minimal RA2CE workflow.)


Quick Start
-----------

.. _quick-start:

Here’s a minimal working example to get you started:

.. code-block:: python

   import ra2ce
   from pathlib import Path
   import geopandas as gpd
   from shapely.geometry import Polygon

   from ra2ce.network import RoadTypeEnum
   from ra2ce.network.network_config_data.enums.network_type_enum import NetworkTypeEnum
   from ra2ce.network.network_config_data.network_config_data import (
       NetworkSection, NetworkConfigData
   )
   from ra2ce.network.network_config_data.enums.source_enum import SourceEnum
   from ra2ce.ra2ce_handler import Ra2ceHandler

   # Define bounding polygon for network extraction
   gdf_polygon_path = Path("data/static/network/polygon.geojson")
   root_dir = Path("ProjectA")

   network_section = NetworkSection(
       source=SourceEnum.OSM_DOWNLOAD,
       network_type=NetworkTypeEnum.DRIVE,
       road_types=[RoadTypeEnum.MOTORWAY, RoadTypeEnum.PRIMARY],
       polygon=gdf_polygon_path,
       save_gpkg=True
   )

   network_config_data = NetworkConfigData(
       root_path=root_dir,
       static_path=root_dir / "static",
       network=network_section
   )

   handler = Ra2ceHandler.from_config(network=network_config_data, analysis=None)
   handler.configure()

To inspect the result, open the files located in ``static/output_graph/`` using QGIS
or load them in Python with ``geopandas``.

From here, you can explore more examples in the :doc:`examples` section.
