.. _faq:

Frequently Asked Questions
==========================

This page contains the most frequently asked questions about working with RA2CE.

Set up RA2CE model
----------------------------
 | **Q**: Where do I store the input data for RA2CE?

Create a folder on your local machine in the RA2CE folder structure with the input data in the correct folder. 
See the :ref:`about` for more information.

 | **Q**: What should my .ini files look like?

The :ref:`network_module` and :ref:`analysis_module` contain all the possible parameters you can specify in the .ini files.
These notebooks give you ideas on which parameters to intialize. This depends on the user's wishes for network creation and/or analyses. 

 | **Q**: What are the minimum data requirements to try a RA2CE model?

The simplest way to try RA2CE is only use the network.ini [network] section and keep all other parameters set to 'None'. 
You can download a network from OSM and specify the required road_types. You only need to create a study area extent and save that geojson in the static/network folder. Then specify that file name in the network.ini file.


Folder structure
----------------------------
 | **Q**: What is the difference between the 'output' and 'static/output_graph' folder? 

The 'output' folder stores the results from the analyses specified in the analyses.ini. 
The output_graph folder stores the created network and the intermediate network information from the network.ini parameters.

Initialization parameters
----------------------------

 | **Q**: How do I know which parameters to specify for the action I want to perform with RA2CE?

The :ref:`network_module` and :ref:`analysis_module` show all the possible parameters you can use in the .ini files. The combination 
of paramaters depends on the purpose for which the user wants to use RA2CE. Using the :ref:`examples_index` the user can get acquainted with 
possible input parameter combinations. 

Network creation
----------------------------

 | **Q**: Can I supply my own shapefile to create the network from?

Yes, absolutely! You can input any shapefile, as long as the lines in the file are connected. RA2CE will convert it to a graph. 

 | **Q**: Can I use RA2CE to only create a network, without running analyses?

Yes you can! You only need to specify the network.ini in this case. 

 | **Q**: I changed my input files but the files in the output_graph folder remain unchanged?

RA2CE does not overwrite the previously created graphs to save computational time. If you want to change the created graph, you should empty the output_graph folder and rerun RA2CE with the new files.

 | **Q**: What is the difference between base_graph_edges and base_network in the output_graph folder?

base_graph_edges is the simplified network. base_network is the segmented network in segments of 100 meter.

 | **Q**: Can I use RA2CE for other networks than roads?

In theory you can use the network module for other networks. The analyses are however specific to the road network. Further network options will be developed in the future. 

Hazard
----------------------------

 | **Q**: Can I only use flood maps?

No, you can use any hazard map, as long as it is in raster format (.tif) and has numerical data.

 | **Q**: How do I do a hazard overlay with the network?

Find a hazard map in the same area as your network. Store it in the static/hazard folder. Specify the parameters in the network.ini. RA2CE will perform a spatial overlay. 

 | **Q**: What do the [hazard] parameters in the network.ini do?

With these settings, you can initialize a hazard map in raster format.

 | **Q**: Where do I find the results of the hazard overlay?

These results are stored in the static/output_graph folder. The results have 'hazard' in their file name. In these files there are columns which hold the hazard's attribute for each edge. 
See :ref:`examples_index` on how to use this in practice. 



Specifying analysis
----------------------------

 | **Q**: How do I pick the analysis/analyses I want to perform?

You can specify the preferred analysis in the analyses.ini file. 
You can choose any analysis and you can initialize multiple at the same time. 
More information can be found in the :ref:`analysis_module` under 'Initialization file templates'. 
There are also examples in the :ref:`examples_index` notebooks.

Direct damage assessment
----------------------------

 | **Q**: Is this module working?

Not yet.


Errors
----------------------------

 | **Q**: What if I get a key error?

This can be caused by a lot of things, but please check your input parameters in the ini files and your input data.

 | **Q**: What if RA2CE cannot find a file?

Check if the file is in the right folder. Check if you specified the path correctly. Check if you specified the file name correctly in the .ini file.
