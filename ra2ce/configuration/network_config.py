import logging
from pathlib import Path
from typing import Dict, Optional

from ra2ce.configuration.configuration_protocol import ConfigurationProtocol
from ra2ce.configuration.validators import NetworkIniConfigurationValidator
from ra2ce.graph.hazard import Hazard
from ra2ce.graph.networks import Network


def network_handler(config: dict, files: dict) -> Optional[dict]:
    try:
        network = Network(config, files)
        graphs = network.create()
        return graphs

    except BaseException as e:
        logging.exception(
            f"RA2CE crashed. Check the logfile for the Traceback message: {e}"
        )
        raise e


def hazard_handler(config: dict, graphs: dict, files: dict) -> Optional[dict]:
    if config["hazard"]["hazard_map"] is not None:
        # There is a hazard map or multiple hazard maps that should be intersected with the graph.
        hazard = Hazard(config, graphs, files)
        graphs = hazard.create()
        return graphs
    else:
        return None


class NetworkConfig(ConfigurationProtocol):
    files: Dict[str, Path] = None

    def __init__(self, ini_file: Path, config_data: dict) -> None:
        self.ini_file = ini_file
        self.config_data = config_data
        self.files = self._get_existent_network_files(
            config_data["static"] / "output_graph"
        )

    @staticmethod
    def get_network_root_dir(filepath: Path) -> Path:
        return filepath.parent.parent

    @staticmethod
    def get_data_output(ini_file: Path) -> Optional[Path]:
        return ini_file.parent / "output"

    @staticmethod
    def _get_existent_network_files(output_graph_dir: Path) -> dict:
        """Checks if file of graph exist in network folder and adds filename to the files dict"""
        _network_filenames = [
            "base_graph.p",
            "base_network.feather",
            "origins_destinations_graph.p",
            "base_graph_hazard.p",
            "origins_destinations_graph_hazard.p",
            "base_network_hazard.feather",
        ]

        def _get_file_entry(expected_file: Path) -> Optional[Path]:
            _value = None
            if expected_file and expected_file.is_file():
                _value = expected_file
                logging.info(f"Existing graph/network found: {expected_file}.")
            return _value

        return {
            _ep.stem: _get_file_entry(_ep)
            for _ep in map(lambda x: output_graph_dir / x, _network_filenames)
        }

    @property
    def root_dir(self) -> Path:
        return self.get_network_root_dir(self.ini_file)

    def configure(self) -> None:
        # Call Handlers (to rework)
        _graphs = network_handler(self.config_data, self.files)
        self.graphs = hazard_handler(self.config_data, _graphs, self.files)

    def is_valid(self) -> bool:
        _file_is_valid = self.ini_file.is_file() and self.ini_file.suffix == ".ini"
        _report = NetworkIniConfigurationValidator(self.config_data).validate()
        return _file_is_valid and _report.is_valid()
