Criticality Analysis
====================

In this chapter, we will guide you through performing a **criticality analysis** on a transport network using RA2CE.
Criticality analysis helps identify how vulnerable your network is to disruptions and which links are most important
for maintaining connectivity.


The criticality module in RA2CE answers questions such as:

1. Is there a viable alternative route if a specific road segment is disrupted?
2. What is the total distance or time of the alternative route?
3. What is the difference in distance or time compared to the original route?

Single Link Redundancy
----------------------

The **single link redundancy** analysis provides insight into the criticality of each individual link in the network.
For each link, the analysis identifies the best existing alternative route in case that link is disrupted.
If no alternative exists, the analysis highlights the lack of redundancy for that link.

This process is performed sequentially for each network link, and the results indicate the degree of redundancy
and potential impact if a specific segment becomes unavailable.


You can learn more and follow the step-by-step instructions in the :doc:`single link redundancy tutorial <criticality.single_link_redundancy>`.

Multi-Link Redundancy
---------------------

The **multi-link redundancy** analysis extends the concept of criticality to situations where multiple links are simultaneously disrupted.
This situation typically occurs when a hazard map is affecting multiple consecutive links. For each disrupted link, RA2CE identifies the best alternative route,
calculates the detour distance or travel time, and flags links without alternatives.

The user can define a threshold for disruption. For example, in flooding scenarios, segments with water depth below 0.5 meters can be ignored.
Segments exceeding the threshold are considered disrupted and included in the multi-link analysis.

Detailed instructions for performing a multi-link redundancy analysis can be found in the :doc:`multi link redundancy tutorial <criticality.multi_link_redundancy>`.

.. toctree::
   :maxdepth: 1

   criticality.single_link_redundancy
   criticality.multi_link_redundancy