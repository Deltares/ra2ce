RA2CE
=====

This is the repository of RA2CE (*just say race!*) - the Resilience Assessment and Adaptation for Critical infrastructurE Toolkit Python Package eveloped by Deltares. RA2CE helps to quantify resilience of critical infrastructure networks, prioritize interventions and adaptation measures and select the most appropriate action perspective to increase resilience considering future conditions.

**Contact** Margreet van Marle (Margreet.vanMarle@Deltares.nl)

Contribution
---------------------------
- Please report to us if you wish to collaborate.
- Use both black and isort (included in the development dependencies) for code formatting.
- Use google docstrings format for documenting your methods and classes.
- New code should come along with new tests verifying its functionality.
- New additions (bug fixes, features, etc) can be done through Pull-requests. Before merging they will be subject to the Continuous Integration builds as well as a code review.

Distribution
---------------------------
Ra2ce is shared with `GPL3 license <https://www.gnu.org/licenses/gpl-3.0.en.html>`__, you may use and / or extend it by using the same license. For specific agreements we urge you to contact us.

Installation
---------------------------
RA2CE can be operated via the command-line interface with two commands. Before RA2CE can be used, the correct Python environment needs to be installed (see *environment.yml*). Anaconda is a well-known environment manager for Python and can be used to install the correct environment and run RA2CE via its command-line interface. It is recommended to install Anaconda, instead of `miniconda`, so that you have all required packages already available during the following steps.

CLI only
+++++++++++++++++++++++++++
If only interested in using the tool via command-line interface follow these steps:
::
  pip install git+https://github.com/Deltares/ra2ce.git
::

Alternatively you can install a specific tag or commit hash from our repo by using the symbol `@`:
::
  pip install git+https://github.com/Deltares/ra2ce.git@v0.3.1
::

Development mode
+++++++++++++++++++++++++++
When running a development environment with Anaconda, the user may follow these steps in command line:
::
  cd <to the main repository RA2CE folder>
  conda env create -f .config\environment.yml
  conda activate ra2ce_env
  poetry install
::

Command-line interface operation
---------------------------
a.	To run both the network creation and analysis modules, run RA2CE with ``python main.py --network_ini <path to network.ini file> --analyses_ini <path to analyses.ini file>``
b.	To only run the network creation module, run RA2CE with ``python main.py --network_ini <path to network.ini file>``
c.	To only run the analysis module, run RA2CE with ``python main.py --analyses_ini <path to analyses.ini file>``

The user can also always ask for clarification of the input arguments with ``python main.py --help``.

Folder structure
---------------------------
RA2CE can be run from anywhere, but it requires a certain folder structure for loading and saving data. RA2CE expects data to be stored separately per project, which can be defined in any way by the user, e.g. by its location in the world or the type of assessment. A project folder must contain the following subfolders: input, output, and static. It must also contain the network.ini and analyses.ini files. Within the subfolder static, RA2CE expects three subfolders: hazard, network, and output_graph. See below an example folder structure of “Project A”. This folder structure must be created and filled with data by the user before running RA2CE.

::

    Project A               --- Example project name 
    ├── input               --- Input data
    ├── output              --- Contains the analyses results
    ├── static              --- Contains files that generally do not change per run
    │   ├── hazard          --- Hazard data
    │   ├── network         --- Network data, e.g. an OSM PBF or GeoJSON file
    │   └── output_graph    --- The resulting network(s) intermediary files that can also be used for quality control
    ├── network.ini         --- Configuration file for the network
    ├── analyses.ini        --- Configuration file for the analyses

Workflow
---------------------------
RA2CE is developed to be used in four ways:

•	Create one or multiple networks *(only run --network_ini)*
•	Calculate the exposure of hazards on those networks *(only run --network_ini)*
•	Execute one or multiple analyses on (a) network(s) *(only run --analyses_ini)*
•	Create a network and execute analyses *(run --network_ini and --analyses_ini)*

To create a network, a network configuration file, also called initialization file, is required. We call this the network.ini file. To execute analyses, an analyses initialization file is required, we call this the analyses.ini file. Both initialization files are required if users want to create a network and execute analyses.

Data requirements
+++++++++++++++++++++++++++
The types of possible input file formats to create a network are:

•	Shapefile of network;
•	GeoJSON polygon of area of interest for downloading a network from OSM;
•	OSM PBF file;
•	Pickle – a python data format, also used to save graphs.

Depending on the required analysis, more data might be needed.

Direct damages
+++++++++++++++++++++++++++
The ‘damage to the network’ depends on the intensity of the hazard in relation to how the network (and its assets) are built and its current condition (e.g. type, state of maintenance, dimensions). Here, the hazard intensity and asset condition are linked to a percentage of damage, via vulnerability functions/ fragility curves. To develop these vulnerability curves data is needed about replacements costs per asset type and the potential damage per hazard intensity. This data can be collected during a workshop with for example national road agencies and the technicians. The output of the analyses consist of damage maps per hazard (e.g. flooding, landslides), per return period or per event, per asset and per road segment.

Possible (built-in) options for vulnerability curves include:

- *Global*: Huizinga curves
- *Europe*: OSdaMage functions
- *TO BE IMPLEMENTED*: your own damage curves

Indirect losses / Network criticality
+++++++++++++++++++++++++++

======================================================   =====================
Analyis                                                   Name in analyses.ini
======================================================   =====================
Single link redundancy                                    single_link_redundancy
Multi-link redundancy                                    multi_link_redundancy
Origin-Destination, defined OD couples, no disruption    optimal_route_origin_destination
Origin-Destination, defined OD couples, disruption       multi_link_origin_destination
Origin-Destination, O to closest D, no disruption        optimal_route_origin_closest_destination
Origin-Destination,  O to closest D, disruption          multi_link_origin_closest_destination
Isolated locations                                       multi_link_isolated_locations 
======================================================   =====================

**Single link redundancy**
This analysis removes each link of the network one at a time. For each disrupted link, a redundancy analysis is performed. It identifies the best existing alternative route or, if there is no redundancy, the lack of alternative routes. This is performed sequentially, for each link of the network. The redundancy of each link is expressed in total distance or time for the alternative route, difference in distance/time between the alternative route and the original route (additional distance/time), and if there is an alternative route available, or not.

**Multi-link redundancy**
This analysis removes multiple disrupted links of the network. The disrupted links are indicated with an overlay of a hazard map and a threshold for disruption. For example, for flooding, the threshold could be a maximum of 0.5 m water on a road segment. For each disrupted link, a redundancy analysis is performed that identifies the best existing alternative route or, if there is no redundancy, the lack of alternative routes. The redundancy of each link is expressed in total distance or time for the alternative route, difference in distance/time between the alternative route and the original route (additional distance/time), and if there is an alternative route available, or not.

**Origin-Destination, defined OD couples**
This analysis finds the shortest (distance-weighed) or quickest (time-weighed) route between all Origins and all Destinations input by the user.

**Origin-Destination, defined origins to closest destinations**
This analysis finds the shortest (distance-weighed) or quickest (time-weighed) route from all Origins to the closest Destinations input by the user.

**Isolated locations**
This analysis finds the sections of the network that are fully isolated from the rest of the network (also named disconnected islands), because of network disruption due to a hazard.

Initialization file templates
+++++++++++++++++++++++++++
**network.ini**
::

    [project]
    name = example

    [network]
    directed = False				# True / False
    source = OSM download			# OSM PBF / OSM download / shapefile / pickle
    primary_file = None				# <name + file extension or full path of file> / None			
    diversion_file = None			# <name + file extension or full path of file> / None
    file_id = None				# <field name of the ID attribute in the shapefile for network creating with a shapefile> / None
    polygon = map.geojson			# <name + file extension of the geojson polygon file in the static/network folder> / None
    network_type = drive			# drive / walk / bike / drive_service / all
    road_types = motorway,motorway_link,trunk,trunk_link,primary, primary_link,secondary,secondary_link,tertiary,tertiary_link
    save_shp = True				# True / False

    [origins_destinations]
    origins = origins.shp 			# <file name> / None
    destinations = destinations.shp		# <file name> / None
    origins_names = A				# <origin name> / None	
    destinations_names = B			# <destination name> / None
    id_name_origin_destination = OBJECTID	# <column name of origins/destinations data ID> / None
    origin_count = None				# <column name> / None
    origin_out_fraction = 1  			# fraction of things/people going out of the origin to the destination

    [hazard]
    hazard_map = None				# <name(s) of hazard maps in the static/hazard folder> / None
    hazard_id = None				# <field name> / None
    hazard_field_name = None			# <field name(s)> / None	
    aggregate_wl = max				# max / min / mean
    hazard_crs = None                           # EPSG code / projection that can be read by pyproj / None

    [cleanup] # use only when the input file is a shapefile
    snapping_threshold = None			# Numeric value / None
    segmentation_length = None			# Numeric value / None
    merge_lines = True				# True / False
    merge_on_id = False				# True / False / None
    cut_at_intersections = False			# True / False


**analyses.ini**
::

  [project]
  name = example

  [analysis1]
  name = single link redundancy test
  analysis = single_link_redundancy
  weighing = distance
  save_shp = True
  save_csv = True

  [analysis2]
  name = multi link redundancy test
  analysis = multi_link_redundancy
  aggregate_wl = max
  threshold = 0.5
  weighing = distance
  save_shp = True
  save_csv = True

  [analysis3]
  name = optimal origin dest test
  analysis = optimal_route_origin_destination
  weighing = distance
  save_shp = True
  save_csv = True

  [analysis4]
  name = multilink origin closest dest test
  analysis = multi_link_origin_closest_destination
  aggregate_wl = max
  threshold = 0.5
  weighing = distance
  save_shp = True
  save_csv = False

  [analysis5]
  name = multilink origin dest test
  analysis = multi_link_origin_destination
  aggregate_wl = max
  threshold = 0.5
  weighing = distance
  save_shp = True
  save_csv = True

  [analysis6]
  name = multilink isolated locations
  analysis = multi_link_isolated_locations
  aggregate_wl = max
  threshold = 1
  weighing = length
  buffer_meters = 40
  category_field_name = category
  save_shp = True
  save_csv = True


Example projects
------------------------------------------------------
`NRT Flood Impact Analysis on Road Networks <https://arcg.is/1uGm5W0>`__ - A case study in the Mandalay region, Myanmar

`Cascading impacts of flooded infrastructure <https://arcg.is/1iC1rX>`__ - Economic quantification for evaluating cascading risks and adaptation solutions

Third-party Notices
------------------------------------------------------
This project incorporates components from the projects listed below.

**NetworkX**: NetworkX is distributed with the `3-clause BSD license <https://opensource.org/license/bsd-3-clause/>`__.

   Copyright (C) 2004-2022, NetworkX Developers
   Aric Hagberg <hagberg@lanl.gov>
   Dan Schult <dschult@colgate.edu>
   Pieter Swart <swart@lanl.gov>
   All rights reserved.

**OSMnx**: OSMnx is distributed under the `MIT License <https://opensource.org/license/mit/>`__.

  Boeing, G. 2017. 
  `OSMnx: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks. <https://geoffboeing.com/publications/osmnx-complex-street-networks/>`__
  Computers, Environment and Urban Systems 65, 126-139. doi:10.1016/j.compenvurbsys.2017.05.004
