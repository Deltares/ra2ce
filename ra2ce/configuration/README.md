# Purpose of this module

Configuration module contains the `Data Object Models` representing a Network and an Analysis configuration.
At the same time, this module also contains the `File Object Models` and their respective readers of the `ini` files that contain
the data for a Network or an Analysis configuration.

The architecture of this module should be such as:
* Data Object Model -> File Object Model -> Readers / Writers

In addition, validators for the File Object Model are also included on this module.

## What goes in this module?
A generic protocol / class concerning a `Configuration`, should be placed in this module. Some cases:
* `IniConfigurationReaderBase`or `IniConfigurationReaderProtocol`which are in configuration\readers
* `IniConfigValidatorBase`: which is in configuration\validators

## What does not go in this module?
As a general rule of thumb, if it is a higher abstraction than configuration, then it should  not be here. Think for instance of:
* `FileReaderProtocol`
* `Ra2ceValidatorProtocol`

This also applies to generic classes that might be used by generic concepts in this module. For instance `NetworkIniConfigReader` or `AnalysisConfigReaderBase` both use the concrete reader `IniFileReader`which is placed in ra2ce\io\readers .