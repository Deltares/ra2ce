# Network

In this package you will find all logic required to load network data from diverse sources (file or web based). 

The configuration to be used to load a network is usually an `.ini` file. This file is later represented as a `NetworkConfigData` object that can as well be directly initialized via code (`network_config_data` (sub)package).

The different sources are handled through our own network wrappers (`NetworkWrapperProtocol`) in the `network_wrappers` (sub)package.


_TODO_
Add class diagram
Add flowchart diagram of loading a diagram