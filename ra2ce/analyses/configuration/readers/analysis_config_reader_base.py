"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


from pathlib import Path

from ra2ce.configuration.readers.ini_config_reader_base import (
    IniConfigurationReaderBase,
)
from ra2ce.configuration.validators.ini_config_validator_base import (
    DirectAnalysisNameList,
    IndirectAnalysisNameList,
)
from ra2ce.common.io.readers.ini_file_reader import IniFileReader


class AnalysisConfigReaderBase(IniConfigurationReaderBase):
    def _convert_analysis_types(self, config: dict) -> dict:
        def set_analysis_values(config_type: str):
            if config_type in config:
                (config[config_type]).append(config[a])
            else:
                config[config_type] = [config[a]]

        analyses_names = [a for a in config.keys() if "analysis" in a]
        for a in analyses_names:
            if any(t in config[a]["analysis"] for t in DirectAnalysisNameList):
                set_analysis_values("direct")
            elif any(t in config[a]["analysis"] for t in IndirectAnalysisNameList):
                set_analysis_values("indirect")
            del config[a]

        return config

    def _import_configuration(self, root_path: Path, config_path: Path) -> dict:
        # Read the configurations in network.ini and add the root path to the configuration dictionary.
        if not config_path.is_file():
            config_path = root_path / config_path
        _config = IniFileReader().read(config_path)
        _config["project"]["name"] = config_path.parent.name
        _config["root_path"] = root_path

        # Set the paths in the configuration Dict for ease of saving to those folders.
        # The output path is set at a different step `IniConfigurationReaderBase::_copy_output_files`
        _config["input"] = config_path.parent / "input"
        _config["static"] = config_path.parent / "static"
        return _config
