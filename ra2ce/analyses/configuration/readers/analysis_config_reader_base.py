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

from ra2ce.common.configuration.ini_configuration_reader_protocol import (
    IniConfigurationReaderProtocol,
)
from ra2ce.configuration.validators.ini_config_validator_base import (
    DirectAnalysisNameList,
    IndirectAnalysisNameList,
)
from ra2ce.common.io.readers.ini_file_reader import IniFileReader
import logging
from pathlib import Path
from shutil import copyfile


class AnalysisConfigReaderBase(IniConfigurationReaderProtocol):
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

    def _copy_output_files(self, from_path: Path, config_data: dict) -> None:
        self._create_config_dir("output", config_data)
        try:
            copyfile(from_path, config_data["output"] / "{}.ini".format(from_path.stem))
        except FileNotFoundError as e:
            logging.warning(e)

    def _create_config_dir(self, dir_name: str, config_data: dict):
        _dir = config_data["root_path"] / config_data["project"]["name"] / dir_name
        if not _dir.exists():
            _dir.mkdir(parents=True)
        config_data[dir_name] = _dir

    def _parse_path_list(
        self, property_name: str, path_list: str, config_data: dict
    ) -> list[Path]:
        _list_paths = []
        for path_value in path_list.split(","):
            path_value = Path(path_value)
            if path_value.is_file():
                _list_paths.append(path_value)
                continue

            _project_name_dir = (
                config_data["root_path"] / config_data["project"]["name"]
            )
            abs_path = _project_name_dir / "static" / property_name / path_value
            try:
                assert abs_path.is_file()
            except AssertionError:
                abs_path = _project_name_dir / "input" / property_name / path_value

            _list_paths.append(abs_path)
        return _list_paths

    def _update_path_values(self, config_data: dict) -> None:
        """
        TODO: Work in progress, for now it's happening during validation, which should not be the case.

        Args:
            config_data (dict): _description_
        """
        _file_types = {
            "polygon": "network",
            "hazard_map": "hazard",
            "origins": "network",
            "destinations": "network",
            "locations": "network",
        }
        for config_header, value_dict in config_data.items():
            if not isinstance(value_dict, dict):
                continue
            for header_prop, prop_value in value_dict.items():
                _prop_name = _file_types.get(header_prop, None)
                if _prop_name and prop_value:
                    config_data[config_header][header_prop] = self._parse_path_list(
                        _prop_name, prop_value, config_data
                    )
