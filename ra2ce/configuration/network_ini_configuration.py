import logging
from pathlib import Path
from typing import Dict, Optional

from ra2ce.configuration.ini_configuration import IniConfiguration
from ra2ce.graph.hazard import Hazard
from ra2ce.graph.networks import Network
from ra2ce.io.readers import IniConfigurationReader


def network_handler(config: dict, files: dict) -> Optional[dict]:
    try:
        network = Network(config, files)
        graphs = network.create()
        return graphs

    except BaseException as e:
        logging.exception(
            f"RA2CE crashed. Check the logfile for the Traceback message: {e}"
        )


def hazard_handler(config: dict, graphs: dict, files: dict) -> Optional[dict]:
    if config["hazard"]["hazard_map"] is not None:
        # There is a hazard map or multiple hazard maps that should be intersected with the graph.
        hazard = Hazard(config, graphs, files)
        graphs = hazard.create()
        return graphs
    else:
        return None


class NetworkIniConfiguration(IniConfiguration):
    files: Dict[str, Path] = None

    def __init__(self, ini_file: Path) -> None:
        if not ini_file.is_file():
            raise FileNotFoundError(ini_file)
        self.ini_file = ini_file
        self.config_data = IniConfigurationReader().import_configuration(
            self.root_dir, config_path=self.ini_file
        )

    @property
    def root_dir(self) -> Path:
        return self.ini_file.parent.parent

    def _set_files(self) -> dict:
        """Checks if file of graph exist in network folder and adds filename to the files dict"""
        _parent_dir = self.config_data["static"] / "output_graph"
        _filename_list = list(
            map(
                lambda x: _parent_dir / x,
                [
                    "base_graph.feather",
                    "base_network.feather",
                    "origins_destinations_graph.p",
                    "base_graph_hazard.p",
                    "origins_destinations_graph_hazard.p",
                    "base_network_hazard.p",
                ],
            )
        )

        self.files = {}
        for _file in _filename_list:
            self.files[_file.stem] = None
            if _file.is_file():
                self.files[_file.stem] = _file
                logging.info(f"Existing graph/network found: {_file}.")

    def configure(self) -> None:
        self._set_files()
        # Call Handlers (to rework)
        _graphs = network_handler(self.config_data, self.files)
        self.graphs = hazard_handler(self.config_data, _graphs, self.files)

    def is_valid(self) -> bool:
        return self.ini_file.is_file() and self.ini_file.suffix == ".ini"
