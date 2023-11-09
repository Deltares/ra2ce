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


import logging
import re
from configparser import ConfigParser
from pathlib import Path
from shutil import copy

from ra2ce.analyses.analysis_config_data.analysis_config_data import (
    AnalysisConfigData,
    AnalysisSection,
    ProjectSection,
)
from ra2ce.analyses.analysis_config_data.analysis_config_data_validator_without_network import (
    DirectAnalysisNameList,
    IndirectAnalysisNameList,
)
from ra2ce.analyses.analysis_config_wrapper.analysis_config_wrapper_base import (
    AnalysisConfigWrapperBase,
)
from ra2ce.common.configuration.ini_configuration_reader_protocol import (
    ConfigDataReaderProtocol,
)


class AnalysisConfigReaderBase(ConfigDataReaderProtocol):
    _parser: ConfigParser

    def __init__(self) -> None:
        self._parser = ConfigParser(inline_comment_prefixes="#")

    def read(self, ini_file: Path) -> AnalysisConfigData:
        if not isinstance(ini_file, Path) or not ini_file.is_file():
            raise ValueError("No analysis ini file 'Path' provided.")
        self._parser.read(ini_file)
        self._remove_none_values()

        _parent_dir = ini_file.parent

        _config_data = AnalysisConfigData(
            input_path=_parent_dir.joinpath("input"),
            static_path=_parent_dir.joinpath("static"),
            output_path=_parent_dir.joinpath("output"),
            **self._get_sections(),
        )
        _config_data.root_path = AnalysisConfigWrapperBase.get_network_root_dir(
            ini_file
        )
        _config_data.project.name = _parent_dir.name
        # TODO self._correct_paths(_config_data)??

        return _config_data

    def _remove_none_values(self) -> None:
        # Remove 'None' from values, replace them with empty strings
        for _section in self._parser.sections():
            _keys_with_none = [
                k for k, v in self._parser[_section].items() if v == "None"
            ]
            for _key_with_none in _keys_with_none:
                self._parser[_section].pop(_key_with_none)

    def _get_sections(self) -> dict:
        return {
            "project": self.get_project_section(),
            "direct": self.get_analysis_sections("direct"),
            "indirect": self.get_analysis_sections("indirect"),
        }

    def get_project_section(self) -> ProjectSection:
        return ProjectSection(**self._parser["project"])

    def _get_analysis_section(self, section_name: str) -> AnalysisSection:
        _section = AnalysisSection(**self._parser[section_name])
        _section.threshold = self._parser.getfloat(
            section_name,
            "threshold",
            fallback=_section.threshold,
        )
        _section.calculate_route_without_disruption = self._parser.getboolean(
            section_name,
            "calculate_route_without_disruption",
            fallback=_section.calculate_route_without_disruption,
        )
        _section.buffer_meters = self._parser.getfloat(
            section_name,
            "buffer_meters",
            fallback=_section.buffer_meters,
        )
        _section.save_gpkg = self._parser.getboolean(
            section_name, "save_gpkg", fallback=_section.save_gpkg
        )
        _section.save_csv = self._parser.getboolean(
            section_name, "save_csv", fallback=_section.save_csv
        )
        return _section

    def get_analysis_sections(self, analysis_type: str) -> list[AnalysisSection]:
        _analysis_sections = []

        _section_names = re.findall(r"(analysis\d)", " ".join(self._parser.keys()))
        for _section_name in _section_names:
            _analysis_name = self._parser.get(_section_name, "analysis")
            if analysis_type == "direct" and _analysis_name in DirectAnalysisNameList:
                _analysis_section = self._get_analysis_section(_section_name)
                _analysis_sections.append(_analysis_section)
            elif (
                analysis_type == "indirect"
                and _analysis_name in IndirectAnalysisNameList
            ):
                _analysis_section = self._get_analysis_section(_section_name)
                _analysis_sections.append(_analysis_section)

        return _analysis_sections

    def _copy_output_files(
        self, from_path: Path, config_data: AnalysisConfigData
    ) -> None:
        _output_dir = config_data.output_path
        if not _output_dir.exists():
            _output_dir.mkdir(parents=True)
        try:
            copy(from_path, _output_dir)
        except FileNotFoundError as e:
            logging.warning(e)

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
