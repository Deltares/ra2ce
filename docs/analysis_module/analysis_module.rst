.. _analysis_module:

Analysis module
================
RA2CE's analysis module can perform several analyses on infrastructure networks. First, a network needs te be created. Visit the :ref:`network_module` for a better understanding of how this works. In the analysis module we distuingish a module focused on direct monetary road damages (damages) and an analysis module for network criticality and origin-destination analyses (losses). The latter are developed from a 'societal losses due to hazards' point of view and provide insight into the hazard impact on the network and the disruption of network services to society. 

Direct/physical damages
-------------------------------------
The physical ‘damage to the network’ depends on the intensity of the hazard in relation to how the network (and its assets) are built and its current condition (e.g. type, state of maintenance, dimensions). Here, the hazard intensity and asset condition are linked to a percentage of damage, via vulnerability functions/ fragility curves. To develop these vulnerability curves data is needed about replacements costs per asset type and the potential damage per hazard intensity. This data can be collected during a workshop with for example national road agencies and the technicians. The output of the analyses consist of damage maps per hazard (e.g. flooding, landslides), per return period or per event, per asset and per road segment.

Possible (built-in) options for vulnerability curves include:

- *Global*: Huizinga curves
- *Europe*: OSdaMage functions
- *TO BE IMPLEMENTED*: your own damage curves

**network.ini**
::

    [project]
    name = example_damages

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = id
    polygon = my_extent.geojson
    network_type = drive
    road_types = motorway, motorway_link
    save_gpkg = True

    [origins_destinations]
    origins = None
    destinations = None
    origins_names = None
    destinations_names = None
    id_name_origin_destination = None
    origin_count = None

    [hazard]
    hazard_map = max_flood_depth.tif
    hazard_id = None
    hazard_crs = EPSG:4326
    aggregate_wl = max

**analysis.ini for an event-based case**
::

    [project]
    name = example_damages
    
    [analysis1]
    name = example's damages analysis
    analysis = direct_damage
    event_type = event
    damage_curve = HZ/OSD/MAN
    aggregate_wl = max
    threshold = 0.5
    weighing = length
    buffer_meters = 500
    category_field_name = category
    save_shp = True
    save_csv = True

**analysis.ini for an occurring event with a wide range of possible return periods**
::

    [project]
    name = example_damages

    [analysis1]
    name = example's damages analysis
    analysis = direct_damage
    event_type = return_period
    risk_calculation = None/default/cut_from_YYYY_year/triangle_to_null_YYYY_year
    damage_curve = HZ/OSD/MAN
    aggregate_wl = max
    threshold = 0.5
    weighing = length
    buffer_meters = 500
    category_field_name = category
    save_shp = True
    save_csv = True

Indirect losses / Network criticality
-------------------------------------

======================================================   =====================
Analysis                                                   Name in analysis.ini
======================================================   =====================
Single link redundancy                                   single_link_redundancy
Multi-link redundancy                                    multi_link_redundancy
Origin-Destination, defined OD couples, no disruption    optimal_route_origin_destination
Origin-Destination, defined OD couples, no disruption    multi_link_origin_destination
Origin-Destination, O to closest D, disruption           optimal_route_origin_closest_destination
Origin-Destination, O to closest D, disruption           multi_link_origin_closest_destination
Isolated locations                                       multi_link_isolated_locations
Equity and traffic analysis                              part of optimal_route_origin_destination    
======================================================   =====================

**Single link redundancy**
With this analysis, you gain insight into the criticality of each link in the network. A redundancy analysis is performed for each seperate link. It identifies the best existing alternative route if that particular edge would be disrupted. If there is no redundancy, it identifies the lack of alternative routes. This is performed sequentially, for each link of the network. The redundancy of each link is expressed in 1) total distance or total time for the alternative route, 2) difference in distance/time between the alternative route and the original route, 3) and if there is an alternative route available, or not.

**network.ini**
::

    [project]
    name = example_losses

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_gpkg = True

**analyses.ini**
::

  [project]
  name = example_losses

  [analysis1]
  name = example_redundancy
  analysis = single_link_redundancy
  weighing = distance
  save_shp = True
  save_csv = True



**Multi-link redundancy**
This analysis provides insight into the impact of a hazard in terms of detour time and alternative route length. This analysis can be performed when there is a hazard map. The hazard map indicates which links are disrupted. The analysis removes multiple disrupted links of the network. For each disrupted link, a redundancy analysis is performed that identifies the best existing alternative route. If there is no redundancy, the lack of alternative routes is specified. The redundancy of each link is expressed in 1) total distance or time for the alternative route, 2) difference in distance/time between the alternative route and the original route (additional distance/time), and 3) whether there is an alternative route available, or not. The user can specify the threshold (in meters) to indicate when a network is considered disrupted. For example, for flooding, the threshold could be a maximum of 0.5 m water on a network segment. Network segments with water depths < 0.5m will then not be considered as flooded.  

**network.ini**
::

    [project]
    name = example_losses

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = None
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_gpkg = True

    [hazard]
    hazard_map = max_flood_depth.tif
    hazard_id = None
    hazard_field_name = waterdepth
    aggregate_wl = max
    hazard_crs = EPSG:32736

**analyses.ini**
::

    [project]
    name = example_losses

    [analysis1]
    name = example_redundancy_multi
    analysis = multi_link_redundancy
    weighing = time
    aggregate_wl = max
    threshold = 0.5
    save_gpkg = True
    save_csv = True

**Origin-Destination, defined OD couples**
RA2CE allows for origin-destination analyses. This analysis finds the shortest (distance-weighed) or quickest (time-weighed) route between all Origins and all Destinations inputted by the user, with and without disruption. The origins and destinations need to be defined by the user. This requires a certain data structure. See the origins-destinations examples notebooks to learn how to do this.  

**network.ini for the case without hazard**
::

    [project]
    name = example_losses

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_gpkg = True

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
    name = example_losses

    [analysis1]
    name = example_od
    analysis = optimal_route_origin_destination
    weighing = distance
    save_gpkg = True
    save_csv = True

**network.ini for the case with hazard**
::

    [project]
    name = example_losses

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
    name = example_losses

    [analysis1]
    name = example_od
    analysis = multi_link_origin_destination
    weighing = distance
    save_gpkg = True
    save_csv = True

**Origin-Destination, defined origins to closest destinations**
This analysis finds the shortest (distance-weighed) or quickest (time-weighed) route from all Origins to the closest Destinations inputted by the user, with and without disruption. It is possible to create different destination categories (e.g. hospitals, schools and shelters). In that case, RA2CE finds the routes from all origins to the closest destination per destination category (i.e. from each origin to the closest hospital, the closest school and the closest shelter). 

**network.ini for the case without hazard**
::

    [project]
    name = example_losses

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_gpkg = True

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
    name = example_losses

    [analysis1]
    name = example_od
    analysis = optimal_route_origin_closest_destination
    weighing = distance
    save_gpkg= True
    save_csv = True

**network.ini for the case with hazard**
::

    [project]
    name = example_losses

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,residential
    save_gpkg = True

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
    name = example_losses

    [analysis1]
    name = example_od
    analysis = multi_link_origin_closest_destination
    aggregate_wl = max
    threshold = 1
    weighing = distance
    calculate_route_without_disruption = True
    save_gpkg = True
    save_csv = True

**Isolated locations**
This analysis finds the sections of the network that are fully isolated from the rest of the network (also named disconnected islands), because of network disruption due to a hazard. <UNDER DEVELOPMENT>

**network.ini**

::

    [project]
    name = example_losses

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,trunk,trunk_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,unclassified,residential
    save_gpkg = True

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

    [project]
    name = example_losses

    [analysis1]
    name = example_locations
    analysis = multi_link_isolated_locations
    aggregate_wl = max
    threshold = 1
    weighing = length
    buffer_meters = 1000
    category_field_name = category
    save_gpkg = True
    save_csv = True


**Traffic and equity analysis**
This analysis allows for network criticality analysis taking into account three distributive equity principles: utilitarian, egalitarian and prioritarian principles. For more background knowledge on these principles and the application on transport network criticality analysis, please read: https://www.sciencedirect.com/science/article/pii/S0965856420308077> The purpose of the equity analysis is providing insight into how different distributive principles can result in different prioritizations of the network. While we usually prioritize network interventions based on the number of people that use the road, equity principles allow us to also take into account the function of the network for for example underpriviliged communities. Depending on the equity principle applied, your network prioritization might change, which can change decision-making.
This analysis is set up generically so that the user can determine the equity weights themselves. This can for example be GINI-coefficients or social vulnerability scores. The user-defined equity weights will feed into the prioritarian principle. The equity analysis example notebook will guide you through the use of this analysis.     

**network.ini**

::

    [project]
    name = example_losses

    [network]
    directed = False
    source = OSM download
    primary_file = None
    diversion_file = None
    file_id = rfid_c
    polygon = Extent_Network_wgs84.geojson
    network_type = drive
    road_types = motorway,motorway_link,trunk,trunk_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,unclassified,residential
    save_gpkg = True

    [origins_destinations]
    origins = origins_points.shp # Must be in the static/network folder, belongs to this analysis. origins should hold counts (e.g. how many people live in the origin)
    destinations = destination_points.shp # Must be in the static/network folder, belongs to this analysis
    origins_names = A
    destinations_names = B
    id_name_origin_destination = OBJECTID 
    origin_count = values #necessary if traffic on each edge should be recorded in optimal_route_origin_destination
    origin_out_fraction = 1
    category = category #column name in destinations specifying the different destination categories (e.g. hospital, school, etc.)
    region = region.shp #a shapefile outlining the reigon's geometry, necessary for distributional / equity analysis
    region_var = DESA #the region's name recorded in a column of the region shapefile

    [hazard]
    hazard_map = None
    hazard_id = None
    hazard_field_name = None
    aggregate_wl = None
    hazard_crs = None


**analyses.ini**

::

    [project]
    name = equity_analysis
    
    [analysis1]
    name = optimal route origin destination
    analysis = optimal_route_origin_destination
    weighing = length
    save_traffic = True #True if you want to record the traffic in each edge
    equity_weight = region_weight.csv #equity-weighted factors for each region, should be stored in static/network. Note that 'region' and 'region_var' should present in network.ini
    save_gpkg = True
    save_csv = True
