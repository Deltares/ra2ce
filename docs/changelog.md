## Unreleased

### Feat

- Create dataclass for `EquityConfigData` (#764)
- Normalize avg speed data (#761)
- Create dataclass for `BaseOriginDestinationConfigData` (#758)
- Created new dataclass `MultiLinkRedundancyConfigData` (#756)
- Create dataclass for `BaseLinkLossesConfigData` (#755)
- create dataclass for `DamagesConfigData` (#746)
- Added new config data for single link redundancy  (#742)
- Origins file make the attribute id name origin destination optional (#728)
- Allow overwrite of output graph folder (#724)
- Added validation for analysis compatibility (#715)
- Origins file make the attribute origin count optional (#723)
- Create an example to run damages and losses without input files (#661)

### Fix

- Investigate failures on master (#770)
- Adaptation analysis config not read correctly (#753)
- Fix build issue (#747)
- Fix matching logic (#744)
- Corrected primary and diversion file property types to `Path` (#727)
- Edited test with external branch (#707)
- Hazard overlay speed improvements (#698)

## v1.0.0 (2025-01-08)

### Feat

- 659 convert damage classes into dataclasses; add a reader for damage curves (#656)
- 636 use same static and output folder of adaptation for dependent analyses (#652)
- 646 write adaptation to file (#650)
- 638 adaptation adaptation analysis should run with only damages or only losses (#642)
- Refactored both analyses to generate an `AnalysisResultWrapper`
- 618 adaptation add option to adaptation config to calculate cost based on fraction segment exposed (#639)
- Create adaptation runner (#634)
- 597 adaptation calculate benefit (#628)
- 457 refactor directanalysisrunner (#624)
- 622 adaptation calculate full link cost (#623)
- 595 adaptation run and combine losses and damages (#616)
- 594 adaptation create and save result cost options (#614)
- 593 calculate unit cost (#613)
- 592 adaptation create class adaptation_option_collection (#609)
-  605 upgrade python version to 311 (#610)
- 604 adaptation extend analysis config dataclass and reader (#607)

### Fix

- create _output_dir if non-existence
- Remove gdal as explicit dependency (#566)

## v0.9.2 (2024-07-17)

### Feat

- 470 refactor losses analysis structure
- 321 skip overlay segmented graph
- 462 docs and other changes
- It is now possible to run an analysis by simply providing dataclasses or ini files. (#461)
- 455 rename runners
- 453 adjust analysis direct
- 451 adjust analysis\indirect
- 449 adjust analysis config data
- gitignore updated
- gitignore updated
- gitignore updated
- representative_damage_percentile added and used to output a representative damage
- divisor added to accept %-based or less-than-one functionality losses in the resilience_curve file
- filter criticality_analysis based on the flood threshold.

### Fix

- 435 fix exception in case no lanes in any of the road types
- 472 fix od analyses using weighing time
- 488 fix weighing time redundancy analyses
- 433 avg speed 0
- 468 set hazard field name to str
- 410 replace simplify graph with OSMNX

## v0.9.1 (2024-04-12)

## v0.9.0 (2024-04-11)

### Feat

- 389 allow an analysis run without files 2nd attempt
- network cleaning simplifying functions PR(#322) - Issue 144
- add hazard cost to the configuration (#406)
- added infrastructure and documentation to allow a cloud run (#398)
- Adapted losses class for `single_link_losses` and `single_link_redundancy`. Included jupyter notebook example. (#383)
- 390 make sections optional (#391)
- Multi link redundancy - adjust calculating diff_time o -diff_length (#393)
- Add time to graph and network (#387)
- Integrated crosscade (#294)

### Fix

- multi link losses document missing test data. (#415)
- running the binder environment examples results in a crash (#409)
- Removed parallel logic that could lead to memory issues (#397)
- Removed parallel logic that could lead to memory issues when running on the cloud or locally
- correct damage_curve field initialization

## v0.8.1 (2024-03-20)

## v0.8.0 (2024-03-20)

### Feat

- Added functionality to directly retrieve the MultiGraph and GeoDataFrame for a given geojson network
- Added static method to directly retrieve a network based on a polygon
- Added result wrapper exporter logic
- Added logic to wrap results of a ra2ce analysis
- partofday Enum is added
- Added logic so that exporting the intermediate results becomes dependent on the existance of the `output_graph_dir` property
- Added endpoint to generate an OsmNetworkWrapper with a fix polygon
- time calculated for the single link redundancy added to the link data
- time calculated for the single link redundancy
- if the link checked in the redundancy is not connected, then time and alt_time is added (for the weight=time) equal to the length/avgspeed.
- add_missing_geometry improved to consider all ks of a multigraph edges
- tracing the origins that are mapped on two graph nodes for instance and have path in one but not in the other

### Fix

- solve bug
- Corrected wrong unknown key to dictionary
- Added logic to callculate time only when strictly required
- minor formatting
- Enum typing added
- Enum is used
- Enum is used
- formatting updated
- Union removed
- deafaultdict list is used
- returning globals() fixed
- float instead of int
- alt_time and length are improved to correspond to the weight stated in the single and multi redundancy
- updated the weight to get correct alt_dist. time is also rounded.
- git ignore is updated to ignore all example outputs

## v0.7.0 (2023-12-05)

### Feat

- minor
- calc_vhl completed. case should be ran. analysis properties are added for Losses
- calc_vhl modified. see 2023-11-24_Sprint: Losses summary onenote
- calc_vhl modified. see 2023-11-24_Sprint: Losses summary onenote
- duration step attribute definition
- calc_vhl chanege started
- minor attribute hints
- minor changes to the Losses
- time and alt_time is added to multi-link redundancy
- time and alt_time is added to multi-link redundancy
- Example notebook is updated
- notebooks are added
- origin closest destination now can be ran without hazard infor in the network and analysis configs

### Fix

- LineString is impoted from shapely.geometry
- docu typos
- `find_route_ods` now returns a geodataframe without duplicate entries or origin_nodes with multiple names
- Changed output suffix.
- save_shp is updated to the output export shapefile

## v0.6.0 (2023-07-28)

### Feat

- Created network wrappers as a separate module
- Extracted logic to generate networks from different sources.

## v0.5.1 (2023-07-26)

### Feat

- **osm_network_wrapper.py**: Adde network wrapper to get a clean network from OSM source.

## v0.5.0 (2023-07-24)

### Feat

- Added dataclass to represent the Network configuration input data (ini file)
- Created stand-alone class for equity analysis
- Implement multi-link isolated locations with distinction between flooded and isolated.

### Fix

- Modified validation to use by default indirect analysis

## v0.4.3 (2023-02-10)

## v0.4.2 (2023-02-10)

### Fix

- **README.rst**: typo fixed, issue #80 thanks Anoek!
- **networks.py**: fix bug #86, ensured the merged_lines object is a GeoDataFrame and not sometimes a Series. Updated related test.

## v0.4.1 (2023-02-09)

### Fix

- **test_acceptance.py**: fixed the test_1_1_given_only_network_shape_redundancy data and added assert statements to networks.py
- **networks_utils.py**: Fixed function get_valid_mean, now it is tested.

## v0.4.0 (2023-02-08)

### Feat

- **ra2ce/analyses/direct/damage_calculation/**: Split previous file into files within a submodule
- **ra2ce/analyses/direct/damage/**: Added damage functions for direct analysis

### Fix

- **networks_utils.py**: Fixed one bug in networks_utils.py for the creation of a network from shp and related test (test_1_1_given_only_network_shape_redundancy).
- **analyses_direct.py;damage_network_base.py**: Removed circular import
- **analyses_direct.py**: Fixed some imports in the analyses_direct.py file

## v0.3.1 (2022-09-26)

### Fix

- **analysis_indirect.py;network_utils.py**: Fixed errors spotted by sonar cloud
- **networks.py;networks_utils.py**: Fixed critical issues spotted by SonarCloud

## v0.3.0 (2022-09-22)

### Feat

- **config_factory; analysis_config_factory**: Split ConfigData creation from IniConfigDataReaders. Introduced factories to deal with the selection criteria for network / analysis and their concrete types

## v0.2.0 (2022-09-21)

### Feat

- **config_reader_factory**: Added factory to reduce responsibilities at a higher level
- Added IniConfigDataProtocol concept
- **ra2ce_handler.py**: Applied Factory patter for analysis runner
- **main.py**: Now we properly check input from comand line
- Moving ra2ce.py logic into class approach

### Fix

- **IniConfigValidatorBase**: Updated config_data parameter type so it's properly casted
- Existen network files were not correctly mapped
- Introduced a small error on a previous refactoring when refering to the parent path of the ini files
- Now we generate networks when no analysis is required
- Network initializes now its own output directories
- **ra2ce.py;utils.py**: Small code reworks to make sure the tests run correctly
- Changed a bit of the logic to ensure a log file is created if not present

### Refactor

- **ra2ce/configuration**: Made the config classes parameterless
- **ra2ce/io/readers**: Extracted concrete readers for better readability
- Inversed logic so it properly respects Single Responsibiltity Principle
- **networks.py**: Removed phased out save_network usages
- **hazard.py**: Removed from hazard phased out save_network
- **network_exporter_factory**: Moved saved_network into more OO aproach
- **json_exporter.py**: Extracted json exporter into separate file / module
- **ra2ce/validation**: Moved out general validation classes to separate module
- renamed and moved checks into proper module
- Removed utils and moved logic into reader for future further refactoring
- **ra2ce/io**: Moved io into its own module
- **ra2ce/runners**: Extracted runners logic into separate module
- **ra2ce/configuration**: Extracted classes into separate m odule
- Replaced previous main with a more OO approach

## v0.1.1 (2022-09-13)

### Fix

- **setup.py**: Encoding for the rst files should be enforced

## v0.0.1-ra2ce_016 (2023-07-24)

## v0.0.1-ra2ce_v1 (2023-07-24)
