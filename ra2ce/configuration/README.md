# Purpose of this module

Configuration module contains **only** protocols (`typing.Protocol`) to represent, for instance a Network or an Analysis configuration (Ini files).

## What goes in this module?
A generic protocol / class concerning a `Configuration`, should be placed in this module. Some cases:
* (DEPRECATED)`IniConfigurationReaderBase`or `IniConfigurationReaderProtocol`which are in configuration\readers
* (DEPRECATED)`IniConfigValidatorBase`: which is in configuration\validators

## What does not go in this module?
As a general rule of thumb, if it is a higher abstraction than configuration, then it should  not be here. Think for instance of:
* `FileReaderProtocol`
* `Ra2ceValidatorProtocol`

This also applies to generic classes that might be used by generic concepts in this module. For instance `NetworkIniConfigReader` or `AnalysisConfigReaderBase` both use the concrete reader `IniFileReader`which is placed in ra2ce\io\readers .