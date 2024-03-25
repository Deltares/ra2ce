# Network

In this (sub-)package you will find all logic required to load network data from diverse sources (file or web based). 

The configuration to be used to load a network is usually an `.ini` file. This file is later represented as a `NetworkConfigData` object that can as well be directly initialized via code (`network_config_data` (sub-)package).

The different sources to generate a network are handled through our own network wrappers (`NetworkWrapperProtocol`) in the `network_wrappers` (sub-)package.


## General class overview

The following diagram describes the relations between the most relevant entities of the `ra2ce.network` (sub-)package.

| ![ra2ce_network_class_diagram.drawio.png](/docs/_diagrams/ra2ce_network_class_diagram.drawio.png)| 
|:--:| 
| *Ra2ce network overview* |