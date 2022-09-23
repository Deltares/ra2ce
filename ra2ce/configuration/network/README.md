# Purpose of this module

Module containing:
* Ini File Reader for an network *.ini file.
* File Object Model for an Network Ini Configuration Data.
* Data Object Model for an Network Configuration.

`NetworkConfiguration` -> contains -> `NetworkIniConfigurationData`
`NetworkIniConfigDataReader` -> reads -> `*.ini` -> into -> `NetworkIniConfigurationData` -> then creates -> `NetworkConfiguration`

## What should go here?
All definitions related to **any** network `ini` configuration file.
When adding a new network configuration it might be needed to update the factories and create new readers and new concrete implementations of an `IniConfigDataProtocol`