.. _analysis_module:

Analysis module
================


Data requirements
-------------------------------------
The types of possible input file formats to create a network are:

•	Shapefile of network;
•	GeoJSON polygon of area of interest for downloading a network from OSM;
•	OSM PBF file;
•	Pickle – a python data format, also used to save graphs.

Depending on the required analysis, more data might be needed. More information about the 
data requirements to create a network can be found in the :ref:`network_module`.

Direct damages
-------------------------------------
The ‘damage to the network’ depends on the intensity of the hazard in relation to how the network (and its assets) are built and its current condition (e.g. type, state of maintenance, dimensions). Here, the hazard intensity and asset condition are linked to a percentage of damage, via vulnerability functions/ fragility curves. To develop these vulnerability curves data is needed about replacements costs per asset type and the potential damage per hazard intensity. This data can be collected during a workshop with for example national road agencies and the technicians. The output of the analyses consist of damage maps per hazard (e.g. flooding, landslides), per return period or per event, per asset and per road segment.

Possible (built-in) options for vulnerability curves include:

- *Global*: Huizinga curves
- *Europe*: OSdaMage functions
- *TO BE IMPLEMENTED*: your own damage curves

Indirect losses / Network criticality
-------------------------------------

======================================================   =====================
Analysis                                                   Name in analyses.ini
======================================================   =====================
Single link redundancy                                   single_link_redundancy
Multi-link redundancy                                    multi_link_redundancy
Origin-Destination, defined OD couples, no disruption    optimal_route_origin_destination
Origin-Destination, defined OD couples, disruption       multi_link_origin_destination
Origin-Destination, O to closest D, no disruption        optimal_route_origin_closest_destination
Origin-Destination,  O to closest D, disruption          multi_link_origin_closest_destination
Isolated locations                                       multi_link_isolated_locations 
======================================================   =====================

**Single link redundancy**
With this analysis, you gain insight into the criticality of the network. A redundancy analysis is performed for each seperate link. It identifies the best existing alternative route if that particular edge would be disrupted. If there is no redundancy, it identifies the lack of alternative routes. This is performed sequentially, for each link of the network. The redundancy of each link is expressed in 1) total distance or total time for the alternative route, 2) difference in distance/time between the alternative route and the original route, 3) and if there is an alternative route available, or not.

**network.ini**
::

    [project]
    name = example

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_shp = True

    [origins_destinations]
    origins = None
    destinations = None
    origins_names = A
    destinations_names = B
    id_name_origin_destination = OBJECTID
    origin_count = PEOPLE
    origin_out_fraction = 1

**analyses.ini**
::

  [project]
  name = example

  [analysis1]
  name = example's analysis
  analysis = single_link_redundancy
  weighing = distance
  save_shp = True
  save_csv = True



**Multi-link redundancy**
This analysis can be performed when there is a hazard map. The hazard map indicates which links are disrupted. The analysis removes multiple disrupted links of the network. For each disrupted link, a redundancy analysis is performed that identifies the best existing alternative route. If there is no redundancy, the lack of alternative routes is specified. The redundancy of each link is expressed in 1) total distance or time for the alternative route, 2) difference in distance/time between the alternative route and the original route (additional distance/time), and 3) whether there is an alternative route available, or not. The user can specify the threshold (in meters) to indicate when a network is considered disrupted. For example, for flooding, the threshold could be a maximum of 0.5 m water on a network segment. Network segments with water depths < 0.5m will then not be considered as flooded.  

**network.ini**
::

    [project]
    name = example

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_shp = True

    [origins_destinations]
    origins = None
    destinations = None
    origins_names = A
    destinations_names = B
    id_name_origin_destination = OBJECTID
    origin_count = PEOPLE
    origin_out_fraction = 1

    [hazard]
    hazard_map = max_flood_depth.tif
    hazard_id = None
    hazard_field_name = waterdepth
    aggregate_wl = max
    hazard_crs = EPSG:32736

**analyses.ini**
::

    [project]
    name = example

    [analysis1]
    name = example's analysis
    analysis = multi_link_redundancy
    weighing = time
    aggregate_wl = max
    threshold = 0.5
    save_shp = True
    save_csv = True

**Origin-Destination, defined OD couples**
This analysis finds the shortest (distance-weighed) or quickest (time-weighed) route between all Origins and all Destinations inputted by the user, with and without disruption. 

**network.ini for the case without hazard**
::

    [project]
    name = example

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_shp = True

    [origins_destinations]
    origins = origins_worldpop_wgs84.shp
    destinations = destinations_all_good_wgs84.shp
    origins_names = A
    destinations_names = B
    id_name_origin_destination = OBJECTID
    origin_count = POPULATION
    origin_out_fraction = 1
    category = category

**analyses.ini for the case without hazard**
::

    [project]
    name = example

    [analysis1]
    name = example's analysis
    analysis = optimal_route_origin_destination
    weighing = distance
    save_shp = True
    save_csv = True

**network.ini for the case with hazard**
::

    [project]
    name = example

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_shp = True

    [origins_destinations]
    origins = origins_worldpop_wgs84.shp
    destinations = destinations_all_good_wgs84.shp
    origins_names = A
    destinations_names = B
    id_name_origin_destination = OBJECTID
    origin_count = POPULATION
    origin_out_fraction = 1
    category = category

**analyses.ini for the case with hazard**
::

    [project]
    name = example

    [analysis1]
    name = example's analysis
    analysis = multi_link_origin_destination
    weighing = distance
    save_shp = True
    save_csv = True

**Origin-Destination, defined origins to closest destinations**
This analysis finds the shortest (distance-weighed) or quickest (time-weighed) route from all Origins to the closest Destinations inputted by the user, with and without disruption. 

**network.ini for the case without hazard**
::

    [project]
    name = example

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_shp = True

    [origins_destinations]
    origins = origins_worldpop_wgs84.shp
    destinations = destinations_all_good_wgs84.shp
    origins_names = A
    destinations_names = B
    id_name_origin_destination = OBJECTID
    origin_count = POPULATION
    origin_out_fraction = 1
    category = category

**analyses.ini for the case without hazard**
::

    [project]
    name = example

    [analysis1]
    name = example's analysis
    analysis = optimal_route_origin_closest_destination
    weighing = distance
    save_shp = True
    save_csv = True

**network.ini for the case with hazard**
::

    [project]
    name = example's analysis

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_shp = True

    [origins_destinations]
    origins = origins_worldpop_wgs84.shp
    destinations = destinations_all_good_wgs84.shp
    origins_names = A
    destinations_names = B
    id_name_origin_destination = OBJECTID
    origin_count = POPULATION
    origin_out_fraction = 1
    category = category

    [hazard]
    hazard_map = max_flood_depth.tif
    hazard_id = None
    hazard_field_name = waterdepth
    aggregate_wl = max
    hazard_crs = EPSG:32736

**analyses.ini for the case with hazard**
::

    [project]
    name = example

    [analysis1]
    name = example's analysis
    analysis = multi_link_origin_closest_destination
    aggregate_wl = max
    threshold = 1
    weighing = distance
    calculate_route_without_disruption = True
    save_shp = True
    save_csv = True

**Isolated locations**
This analysis finds the sections of the network that are fully isolated from the rest of the network (also named disconnected islands), because of network disruption due to a hazard.

**network.ini**
::
    [project]
    name = example

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,trunk,trunk_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,unclassified,residential
    save_shp = True

    [origins_destinations]
    origins = origins_worldpop_wgs84.shp
    destinations = destinations_all_good_wgs84.shp
    origins_names = A
    destinations_names = B
    id_name_origin_destination = OBJECTID
    origin_count = POPULATION
    origin_out_fraction = 1
    category = category

    [hazard]
    hazard_map = max_flood_depth.tif
    hazard_id = None
    hazard_field_name = waterdepth
    aggregate_wl = max
    hazard_crs = EPSG:4326

    [isolation]
    locations = origins_worldpop_wgs84.shp

**analyses.ini**
::
    project]
    name = example

    [analysis1]
    name = example's analysis
    analysis = multi_link_isolated_locations
    aggregate_wl = max
    threshold = 1
    weighing = length
    buffer_meters = 1000
    category_field_name = category
    save_shp = True
    save_csv = True