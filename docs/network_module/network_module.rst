.. _network_module:

Network Module
==============

The network module is separate module created within `ra2ce` to help set up a RA2CE 
model. It helps to easily, reproducibly and consistently build models from global 
to local datasets.

Network from OpenStreetMap
----------------------------


This functionality is built on top of the `osmnx` package. The method  uses the `osmnx`
package to download and process the road network data. It then uses the
`osmnx` package to calculate the accessibility metrics. The network module
provides a wrapper around the `osmnx` package to make it easier to use.

(:py:class:`~ra2ce.graph.network_wrappers.osm_network_wrapper.osm_network_wrapper.OsmNetworkWrapper`) 

Reference to function :py:class:`~ra2ce.graph.network_wrappers.osm_network_wrapper.osm_network_wrapper.OsmNetworkWrapper`

Network from vector data
----------------------------



Usage
----------------------------

Create capabilities so that a user can specify a geographic region of interest, 
a minimal number of model-specific parameters and a model to quantify impacts 
on roads and accessibility (RA2CE) is automatically set up using globally available data
