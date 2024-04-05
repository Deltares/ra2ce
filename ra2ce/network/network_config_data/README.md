# Network config data

In this package we contain the representation of a network configuration file, its readers and validators.

- `network_config_data.py` contains the main `dataclass` `NetworkConfigData` which has the properties representing each of the different INI sections as `dataclasses`.
- `network_config_data_validator.py` contains the logic to validate all properties of a `NetworkConfigData`.
- `network_config_data.py` contains the `NetworkConfigDataReader`, an `*.ini` file reader that parses its content into an instance of a `NetworkConfigData`.