.. _about:

RA2CE
=====

This is the repository of RA2CE (*just say race!*) - the Resilience Assessment and Adaptation for Critical 
infrastructurE Toolkit Python Package eveloped by Deltares. RA2CE helps to quantify resilience of critical 
infrastructure networks, prioritize interventions and adaptation measures and select the most appropriate 
action perspective to increase resilience considering future conditions.

**Contact** Lakshman Srikanth (Lakshman.srikanth@deltares.nl) or Margreet van Marle (Margreet.vanMarle@Deltares.nl)


Distribution
---------------------------
Ra2ce is shared with `GPL3 license <https://www.gnu.org/licenses/gpl-3.0.en.html>`__, you may use and / or 
extend it by using the same license. For specific agreements we urge you to contact us.



Within a Python script
---------------------------
To use Risk Assessment and Adaptation for Critical infrastructurE in a project::

    import ra2ce


Folder structure
---------------------------
RA2CE can be run from anywhere, but it requires a certain folder structure for loading and saving data. RA2CE expects 
data to be stored separately per project, which can be defined in any way by the user, e.g. by its location in the 
world or the type of assessment. A project folder must contain the following subfolders: output, and static. Within the subfolder static, RA2CE expects three subfolders:
hazard, network, and output_graph. See below an example folder structure of “Project A”. This folder structure must be 
created and filled with data by the user before running RA2CE.

::

    Project A               --- Example project name 
    ├── output              --- Contains the analyses results
    ├── static              --- Contains files that generally do not change per run
    │   ├── hazard          --- Hazard data
    │   ├── network         --- Network data, e.g. an OSM PBF or GeoJSON file
    │   └── output_graph    --- The resulting network(s) intermediary files that can also be used for quality control

Workflow
---------------------------
RA2CE is developed to be used in four ways:

•	Create one or multiple networks *(only run --network_ini)*
•	Calculate the exposure of hazards on those networks *(only run --network_ini)*
•	Create a network and execute analyses *(run --network_ini and --analyses_ini)*
•   Execute one or multiple analyses on a previously created network *(run --analyses_ini)*

To create a network, a network configuration file, also called initialization file, is required. We call 
this the network.ini file. To execute analyses, an analyses initialization file is required, we call this 
the analyses.ini file. Both initialization files are required if users want to create a network and execute analyses.

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
