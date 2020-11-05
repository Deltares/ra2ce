==========================================================
Risk Assessment and Adaptation for Critical infrastructurE
==========================================================


.. image:: https://img.shields.io/pypi/v/ra2ce.svg
        :target: https://pypi.python.org/pypi/ra2ce

.. image:: https://img.shields.io/travis/mjevanmarle/ra2ce.svg
        :target: https://travis-ci.com/mjevanmarle/ra2ce

.. image:: https://readthedocs.org/projects/ra2ce/badge/?version=latest
        :target: https://ra2ce.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


.. image:: https://pyup.io/repos/github/mjevanmarle/ra2ce/shield.svg
     :target: https://pyup.io/repos/github/mjevanmarle/ra2ce/
     :alt: Updates



Risk Assessment  and Adaptation for Critical infrastructurE.


* Free software: GNU General Public License v3
* Documentation: https://ra2ce.readthedocs.io.


Features
--------

# RA2CE

Risk Assessment and Adaptation for Critical InfrastructurE (RA2CE) is a tool developed by Deltares for calculating damages and losses for infrastructure networks resulting from hazards.

The tool consists currently of four components:
- Network creation
- Exposure
- Criticality
- Damages

-Prioritization - to be implemented
-Adaptation - to be implemented

The user needs to decide which analysis should be performed:
- Direct damages 
- Redundancy-based criticality
- Both

Both Direct damanges and Redundancy-based criticality have their own functionalities. See for more detail below.

Contact details: RA2CE Margreet van Marle (Margreet.vanMarle@Deltares.nl), Direct Damages: Kees van Ginkel (Kees.vanGinkel@Deltares.nl, Criticality: Frederique de Groen (Frederique.deGroen@Deltares.nl)

## Network Creation
THe user needs to decide which type of input data will be used to create the infrastructure network. Currently the following 3 methods are implemented
- *Create a network based on OSM dump file* (.osm.pbf) -  The user needs to identify the name of the OSM dump and a shapefile containing the area of interest. 
- *Create a network based on a shapefile*  - The user needs to deliver a shapefile and indicate the column of the unique identifier.

(- Create a network based on OSM online download) - to be implemented

## Exposure
For every hazard map an exposure map will be created, where exposure is defined as the overlay between the infrastructure network and the hazard map. In case of a flooding on road-infrastructure this will for example result in a map with the waterdepth projected on the road. The exposure value is based on the average value of the hazard data intersecting with the infrastructure element. The user can choose what size the segments should be based on a segmentation script. This should be given in degree. 

## Criticality
This module calculated the redundancy based criticality
There are three possible analyses.

**1. Single-link Disruption**
What is the effect of disruption when a single link for the redundancy of the system.  In this analysis, each link of the network is disrupted at a time. For each disrupted link, a redundancy analysis is performed that identifies the best existing alternative or, if there is no redundancy, the lack of alternative routes. This is performed sequentially, for each link of the network. It is also possible to focus on a specific network level and use the remaining existing links as detour possibilities: such distinction can be chosen in a subsequent question.

**2. Multi-link Disruption (1): Calculate the disruption for all damaged roads**
Multiple link disruption can be analyzed making use of a hazard map. This can be a hazard map with a return interval or it can be an event-based approach.
In this analysis, a group of multiple links are removed simultaneously. While the group disruption is in place, alternative routes connecting the end-points of each link of the group is identified. This is a redundancy analysis for each link of the network when multiple parts of the network are out of operation and can be used to simulate area covering events such as specific flooding or earthquakes. Also can be identified whether groups of the network are isolated.

**3. Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix**
When origin and destination files are provided 

When infrastructure usage data are available it is also possible to calculate the losses. The user should provide these data in the excel file: <NAME excel fie>

## Damages - to be implemented
**vulnerability curves**
The user will need to identify the vulnerability curves for the hazard intensity and damage based on the following table: .xlsx

## Risk prioritization - to be implemented
# Installation
in PYcharm use the ra2ce.yml file to set up an environment. This is running on Python 3.7. The python interpreter should be based on ra2ce.
Furthermore the user should set the working directory to the main ra2ce folder: not ra2ce/ra2ce/ra2ce (where the ra2ce script is located).

## Testing
Test files are standard refered to in the ra2ce.py (main script). This will perform a multi-link diruption based on a map in the dominican republic.

## Config file
Standard the utils.py directs to the test_config.json file. When the test is exiting without errors, the user should change this to config.json to perform their own analysis.

# User input
THe user needs to fill out the document to_fill_in.xlsx and has to choose for several options. Multiple analysis can be done: add another row with settings for the different calculations.
Below is an overview of the user input variables. All relative paths are described in the Config file.
All geospatial files should be projected in EPSG: 4326

## analysis_name
Name that you want to give to the analysis (output files will start with this name)

## analysis
Choose from: 
- *Direct Damages*
- *Redundancy-based criticality*
- *Both*

## links_analysis
Only when chosen for *Redundancy-based criticality* or *Both*

Choose from:
- *Single-link Disruption*
- *Multi-link Disruption (1): Calculate the disruption for all damaged roads*
- *Multi-link Disruption (2): Calculate the disruption for an Origin/Destination matrix*

## network_source
Choose how the network will be created. 
Choose from:
- *Network based on shapefile* - user needs to provide shapefile with network and indicate the attribute with unique_ID at **shp_input_data** and **shp_unique_ID** in input table
- *Network based on OSM dump* - user needs to provide .shp file with area of interest at **OSM_area_of_interest** in input table
- *Network based on OSM online* - user needs to provide .shp file with area of interest at **OSM_area_of_interest** in input table

## OSM_area_of_interest
When choosing **network_source** *Network based on OSM dump* or *Network based on OSM online* provide name of shapefile with region for OSM input. 

## shp_input_data
When choosing **network_source** *Network based on shapefile* provide name of shapefile with with the infrastructure network.

## shp_unique_ID
When choosing **network_source** *Network based on shapefile* provide name of shapefile at **shp_input_data** and indicate here the column of the shapefile with the Unique_ID. In case no unique ID exists, leave this cell empty and the tool will create a new one.

## shp_for_diversion
In case you would like to make use of the underlying network for diversions, add here the shapefile used for that.

## data_manipulation
When choosing **network_source** *Network based on shapefile* indicate whether the shapefile should be fixed for unconnected lines. After performing this analysis, the user should check out the result via shapefile based on visual inspection. Choose from:
- *snapping*
- *pruning*
- *snapping,pruning*

## snapping_threshold
When choosing **network_source** *Network based on shapefile* and **data_manipulation** *snapping* or *snapping,pruning* please indicate the threshold for snapping. This value should be given in degree.

## network_type
Choose from:
- *walk*
- *bike*
- *drive*
- *drive_service*
- *all*

When left empty default is: XXXXX

## road_types -> **change to infrastructure_type?**
Here the user can specify which network_types are included in the network. These can be used for creation of the vulnerability curve input sheets. **andere dingen ook nog?**
When left empty default is **XXXXXX**
Anny option is valid, but these are some commmon types:
- *motorway, trunk, primary, secondary, tertiary*
- *motorway, trunk, primary, secondary*
- *motorway, trunk, primary*
- *motorway, trunk*
- *motorway*
- *add another option here*

## hazard_data
When including hazard data, provide the specific filenames, separated by comma. The tool can handle both *.shp* and *.tif* files. By default, the tool uses all files in the hazard folder (see **config**) ending at *.tif*, or *.shp*

## hazard_attribute_name
In case **hazard_data** of .shp hazard map indicate the column of the attribute that represents the hazard intensity.

## hazard_unique_ID
In case the **hazard_data** can be linked to the infrastructure network by unique_ID similar to **shp_unique_id** indicate here the column of the unique ID in the hazard shapefile .

## hazard_unit
Indicate here the units for the hazard intensity described in **hazard_attribute_name**

## hazard_aggregation
When translating the hazard intensity to the infrastructure network, indicate how the hazard intensity should be determined in case of crossing multiple hazard intensities. It can include the following options 
- *max*
- *min*
- *mean*

in case of multiple analyses, separate by comma.

## segmentation
When translating the hazard intensity to the infrastructure network, indicate at which length of infrastructure lines the direct damages should be projected. The length of the segments should be given in degree.By default a node-to-node value will be determined based on the given input in **hazard_aggregation**.

## hazard_threshold
in the unit of the hazard map

## origin_shp
**add text on origin and destination analysis** name of the file(s) for the point data that can be used as origins (must be shapefiles) - do not add file extension

## destination_shp
name of the file(s) for the point data that can be used as destinations (must be shapefiles) - do not add file extension

## id_name_origin_destination
name of the attribute that is the Unique ID in both origin shapefiles and destination shapefiles

## infra_usage -> ik zag deze niet staan in het excel bestand @frederique
file names where information on infrastructure usage is stored: the Average Annual Daily Traffic and costs per vehicle type

## vulnerability_functions --> deze moet nog toegevoegd!




Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
