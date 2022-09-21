# Purpose of this module

Module containing:
* Ini File Reader for an analysis *.ini file.
* File Object Model for an Analysis Ini Configuration Data.
* Data Object Model for an Analysis Configuration.

`AnalysisConfiguration` -> contains -> `AnalysisIniConfigurationData`
`AnalysisIniConfigurationReader` -> reads -> `*.ini` -> into -> `AnalysisIniConfigurationData` -> then creates -> `AnalysisConfiguration`

## What should go here?
All definitions related to **any** analysis `ini` configuration file.
When adding a new analysis configuration it might be needed to update the factories and create new readers and new concrete implementations of an `IniConfigDataProtocol`