# RA2CE

Risk Assessment and Adaptation for Critical InfrastructurE (RA2CE) is a tool developed by Deltares for calculating damages and losses for infrastructure networks resulting from hazards.

The tool consists currently of four components:
- Network creation
- Exposure
- Criticality
- Damages

(-Prioritization to be implemented)

THe user needs to decide which analysis should be performed:
- Direct damages 
- Redundancy-based criticality
- Both

Both Direct damanges and Redundancy-based criticality have their own functionalities.

## Network Creation
THe user needs to decide which type of input data will be used to create the infrastructure network. Currently the following 3 methods are implemented
- Create a network based on OSM dump file (.osm.pbf)
- Create a network based on OSM online download
- Create a network based on a shapefile

## Exposure
For every hazard map an exposure map will be created, where exposure is defined as the overlay between the infrastructure network and the hazard map. In case of a flooding on road-infrastructure this will for example result in a map with the waterdepth projected on the road.

## Criticality
This module calculated the redundancy based criticality. There are three possible analyses.
1. 

When infrastructure usage data are available it is also possible to calculate the losses.

## Damages


## Risk prioritization

# Pre-processing

# User input
THe user needs to fill out the document to_fill_in.xlsx and has to choose between the following options
