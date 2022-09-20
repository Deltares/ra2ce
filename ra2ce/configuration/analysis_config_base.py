from pathlib import Path
from typing import Dict, Optional

from ra2ce.configuration.ini_configuration_protocol import IniConfigurationProtocol


class AnalysisConfigBase(IniConfigurationProtocol):
    ini_file: Path
    root_dir: Path
    config_data: Dict = None

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
            if not analysis_type in self.config_data.keys():
                return
            for a in self.config_data[analysis_type]:
                output_path = self.config_data["output"] / a["analysis"]
                output_path.mkdir(parents=True, exist_ok=True)

        _create_output_folders("direct")
        _create_output_folders("indirect")
