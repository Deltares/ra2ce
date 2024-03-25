# Changelog

## v0.8.1 (2024-03-20)

## v0.8.0 (2024-03-20)

### Feat

- Added functionality to directly retrieve the MultiGraph and GeoDataFrame for a given geojson network
- Added static method to directly retrieve a network based on a polygon
- Added result wrapper exporter logic
- Added logic to wrap results of a ra2ce analysis
- Partofday Enum is added
- Added logic so that exporting the intermediate results becomes dependent on the existance of the `output_graph_dir` property
- Added endpoint to generate an OsmNetworkWrapper with a fix polygon
- Time calculated for the single link redundancy added to the link data
- Time calculated for the single link redundancy
- If the link checked in the redundancy is not connected, then time and alt_time is added (for the weight=time) equal to the length/avgspeed.
- add_missing_geometry improved to consider all ks of a multigraph edges
- Tracing the origins that are mapped on two graph nodes for instance and have path in one but not in the other
- calc_vhl modified. see 2023-11-24_Sprint: Losses summary onenote
- Duration step attribute definition
- Minor changes to the Losses
- Time and alt_time is added to multi-link redundancy

### Fix

- Corrected wrong unknown key to dictionary
- Added logic to calculate time only when strictly required
- alt_time and length are improved to correspond to the weight stated in the single and multi redundancy
- Updated the weight to get correct alt_dist. time is also rounded.
- LineString is imported from shapely.geometry

## v0.7.0 (2023-12-05)

### Feat

- Example notebook is updated
- notebooks are added
- origin closest destination now can be ran without hazard infor in the network and analysis configs

### Fix

- docu typos
- `find_route_ods` now returns a geodataframe without duplicate entries or origin_nodes with multiple names
- Changed output suffix.
- save_shp is updated to the output export shapefile

## v0.6.0 (2023-07-28)

### Feat

- Created network wrappers as a separate module
- Extracted logic to generate networks from different sources.
- **osm_network_wrapper.py**: Adde network wrapper to get a clean network from OSM source.
- Added dataclass to represent the Network configuration input data (ini file)

## v0.5.1 (2023-07-26)

### Feat

- Implement multi-link isolated locations with distinction between flooded and isolated.

## v0.5.0 (2023-07-24)

### Feat

- Created stand-alone class for equity analysis

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
