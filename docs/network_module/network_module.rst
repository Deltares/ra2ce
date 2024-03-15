.. _network_module:

Network Module
==============

The network module is a separate module created within `RA2CE` to help set up a RA2CE 
model. It helps to easily, reproducibly and consistently build models from global 
to local datasets. The network module's goal is to create an infrastructure network to be used in further analyses. There are two possibilities to create a network: 1) downloading a network from OpenStreetMap with RA2CE and 2) creating a network from vector data. Within the network module, it is additionally possible to determine the network's exposure to a user-specified hazard using the 'hazard overlay' functionality. 

Network from OpenStreetMap using scripting
-----------------------------------------------------------------------------

The :py:class:`~ra2ce.graph.network_wrappers.osm_network_wrapper.osm_network_wrapper.OsmNetworkWrapper` 
class can download and process OpenStreetMap data for a given region of interest, using the `osmnx` 
package. The region of interest must be specified with a GeoJSON file.

Additional functionalities in the :py:class:`~ra2ce.graph.network_wrappers.osm_network_wrapper.osm_network_wrapper.OsmNetworkWrapper` 
class include:
- Filtering the OSM data on (road) type
- Assigning the average speed of a road segment based on the maximum speed limit data and road type from OSM
- Adding the missing geometries of the edges (road segments) based on the nodes (intersections)
- Dropping duplicates in nodes and edges
- Snapping nodes to the nearest nodes in the network considering a given threshold
- Snapping nodes to the nearest edges in the network considering a given threshold
- Adding the missing nodes and edges to the network based on the snapped nodes and edges

Examples of how to use this module can be found in the :ref:`examples`.

Network from OpenStreetMap using initalization file network.ini
-----------------------------------------------------------------------------




Network from vector data
----------------------------

There are three ways to create a network from vector data. The first is to clean the 
data yourself before using the Network Module and to then use the :py:class:`~ra2ce.graph.network_wrappers.vector_network_wrapper.VectorNetworkWrapper`
class to read and process the data (e.g., a GeoPackage) to a network. The second 
is to use the :py:class:`~ra2ce.graph.network_wrappers.shp_network_wrapper.ShpNetworkWrapper`
class to read in a shapefile, clean it and process it to a network.

The user can also read in a pre-defined shapefile using the ra2ce_basics_shapefile example notebook, where the user can practice with pre-defined data and required folder structure and data format. 

Network overlay with hazard data
--------------------------------

It is possible to perform overlays with hazard data and the network. RA2CE can handle any hazard data in .tif format. It will return information on where the hazard touches the network and give the hazard attribute to the network (e.g. flood depth on a road segment). RA2CE can use this information to determine the impact of a hazard on the network and on the routes between origins-destinations. Check the examples to see how to use it. 
