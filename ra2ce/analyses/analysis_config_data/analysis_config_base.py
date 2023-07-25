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
from typing import Optional

from ra2ce.analyses.analysis_config_data.analysis_ini_config_data import AnalysisConfigData
from ra2ce.common.configuration.config_wrapper_protocol import ConfigWrapperProtocol


class AnalysisConfigBase(ConfigWrapperProtocol):
    ini_file: Path
    root_dir: Path
    config_data: Optional[AnalysisConfigData] = None

    @staticmethod
    def get_network_root_dir(filepath: Path) -> Path:
        return filepath.parent.parent

    @staticmethod
    def get_data_output(ini_file: Path) -> Optional[Path]:
        _root_path = AnalysisConfigBase.get_network_root_dir(ini_file)
        _project_name = ini_file.parent.name
        return _root_path / _project_name / "output"

    @property
    def root_dir(self) -> Path:
        return self.get_network_root_dir(self.ini_file)

    def initialize_output_dirs(self) -> None:
        """
        Initializes the required output directories for a Ra2ce analysis.
        """

        def _create_output_folders(analysis_type: str) -> None:
            # Create the output folders
            if analysis_type not in self.config_data.keys():
                return
            for a in self.config_data[analysis_type]:
                output_path = self.config_data["output"] / a["analysis"]
                output_path.mkdir(parents=True, exist_ok=True)

        _create_output_folders("direct")
        _create_output_folders("indirect")
