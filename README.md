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

## Network Creation
THe user needs to decide which type of input data will be used to create the infrastructure network. Currently the following 3 methods are implemented
**Create a network based on OSM dump file (.osm.pbf)**
The user needs to identify the name of the OSM dump and a shapefile containing the area of interest. 
**Create a network based on a shapefile**


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

# User input
THe user needs to fill out the document to_fill_in.xlsx and has to choose for several options. See overview of options below.

# Pre-processing of data
The data should be provided in the file format as mentioned in the input table.

