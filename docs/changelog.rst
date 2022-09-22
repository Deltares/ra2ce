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

## v0.1.0 (2020-09-25)
------------------

* First release on PyPI.